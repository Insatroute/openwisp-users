(function () {
  "use strict";

  var SESSION_CHECK_INTERVAL = 30000; // check every 30 seconds

  function checkSession() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/accounts/session-activity/", true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4 || xhr.status !== 200) return;
      try {
        var data = JSON.parse(xhr.responseText);
      } catch (e) {
        return;
      }
      if (!data.authenticated || data.remaining <= 0) {
        window.location.href = "/account/login/?session_expired=1";
      }
    };
    xhr.send();
  }

  function init() {
    checkSession();
    setInterval(checkSession, SESSION_CHECK_INTERVAL);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
