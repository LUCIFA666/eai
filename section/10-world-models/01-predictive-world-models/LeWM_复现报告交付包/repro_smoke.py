"""Strictly load and exercise the released Push-T LeWM checkpoint."""

import argparse
import json
import os
from pathlib import Path

import stable_pretraining as spt
import stable_worldmodel as swm
import torch

from jepa import JEPA
from module import ARPredictor, Embedder, MLP, SIGReg


def parse_args():
    cache_root = Path(os.environ.get("STABLEWM_HOME", Path.home() / ".stable-wm"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=cache_root / "hf_pusht")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=cache_root / "checkpoints" / "pusht" / "lewm",
    )
    parser.add_argument(
        "--device",
        default="cuda" if torch.cuda.is_available() else "cpu",
    )
    parser.add_argument("--batch-size", type=int, default=2)
    return parser.parse_args()


def build_model(cfg):
    encoder = spt.backbone.utils.vit_hf(
        cfg["encoder"]["size"],
        patch_size=cfg["encoder"]["patch_size"],
        image_size=cfg["encoder"]["image_size"],
        pretrained=False,
        use_mask_token=False,
    )

    def mlp(name):
        values = cfg[name]
        return MLP(
            input_dim=values["input_dim"],
            output_dim=values["output_dim"],
            hidden_dim=values["hidden_dim"],
            norm_fn=torch.nn.BatchNorm1d,
        )

    return JEPA(
        encoder=encoder,
        predictor=ARPredictor(
            **{key: value for key, value in cfg["predictor"].items() if key != "_target_"}
        ),
        action_encoder=Embedder(
            **{
                key: value
                for key, value in cfg["action_encoder"].items()
                if key != "_target_"
            }
        ),
        projector=mlp("projector"),
        pred_proj=mlp("pred_proj"),
    )


def main():
    args = parse_args()
    cfg = json.loads((args.source / "config.json").read_text())
    model = build_model(cfg)
    state = torch.load(args.source / "weights.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(state, args.output_dir / "weights.pt")
    (args.output_dir / "config.json").write_text(
        json.dumps(cfg, indent=2) + "\n"
    )
    # Keep an object checkpoint too, for the README's AutoCostModel API.
    object_checkpoint = args.output_dir / "lewm_object.ckpt"
    torch.save(model, object_checkpoint)

    device = torch.device(args.device)
    model = model.to(device).eval()
    batch_size = args.batch_size
    frames = cfg["predictor"]["num_frames"] + 1
    image_size = cfg["encoder"]["image_size"]
    action_dim = cfg["action_encoder"]["input_dim"]
    generator = torch.Generator(device=device).manual_seed(3072)
    batch = {
        "pixels": torch.randn(
            batch_size,
            frames,
            3,
            image_size,
            image_size,
            generator=generator,
            device=device,
        ),
        "action": torch.randn(
            batch_size,
            frames,
            action_dim,
            generator=generator,
            device=device,
        ),
    }

    with torch.inference_mode():
        output = model.encode(batch)
        prediction = model.predict(
            output["emb"][:, :-1], output["act_emb"][:, :-1]
        )
        target = output["emb"][:, 1:]
        prediction_loss = (prediction - target).square().mean()
        sigreg_loss = SIGReg(knots=17, num_proj=1024).to(device)(
            output["emb"].transpose(0, 1)
        )

    assert prediction.shape == target.shape
    assert torch.isfinite(prediction_loss)
    assert torch.isfinite(sigreg_loss)

    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    print(f"strict_load=ok")
    print(f"device={device}")
    print(f"parameters={parameter_count}")
    print(f"embedding_shape={tuple(output['emb'].shape)}")
    print(f"prediction_shape={tuple(prediction.shape)}")
    print(f"prediction_loss={prediction_loss.item():.6f}")
    print(f"sigreg_loss={sigreg_loss.item():.6f}")
    print(f"checkpoint_dir={args.output_dir}")
    print(f"object_checkpoint={object_checkpoint}")

    # Exercise both the current eval.py loader and the legacy README API.
    loaded = swm.wm.utils.load_pretrained(str(args.output_dir))
    loaded.load_state_dict(model.cpu().state_dict(), strict=True)
    print("stable_worldmodel_loader=ok")
    cost_model = swm.policy.AutoCostModel(str(args.output_dir))
    cost_model.load_state_dict(model.state_dict(), strict=True)
    print("auto_cost_model_loader=ok")

    # Exercise the cost path consumed by the MPC solver with two candidates.
    candidates = 2
    horizon = 5
    history = cfg["predictor"]["num_frames"]
    planning_info = {
        "pixels": torch.randn(
            1, candidates, history, 3, image_size, image_size
        ),
        "goal": torch.randn(1, candidates, 1, 3, image_size, image_size),
        "action": torch.zeros(1, candidates, history, action_dim),
    }
    action_candidates = torch.randn(
        1, candidates, horizon, action_dim, device=device
    )
    cost_model = cost_model.to(device)
    with torch.inference_mode():
        costs = cost_model.get_cost(planning_info, action_candidates)
    assert costs.shape == (1, candidates)
    assert torch.isfinite(costs).all()
    print(f"mpc_cost_shape={tuple(costs.shape)}")
    print("mpc_cost=ok")


if __name__ == "__main__":
    main()
