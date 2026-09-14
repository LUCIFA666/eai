// reload.js — 轻量自动刷新：轮询当前页所在章子树的最大 mtime，变化即刷新。
// 仅本地开发用，无 websocket；服务器端点见 serve_docs.py 的 /__mtime。
(function () {
  var last = null;
  function check() {
    fetch("/__mtime?path=" + encodeURIComponent(location.pathname))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (last !== null && d.mtime > last) { location.reload(); }
        last = d.mtime;
      })
      .catch(function () { /* 服务器未就绪时静默重试 */ });
  }
  setInterval(check, 1000);
  check();
})();
