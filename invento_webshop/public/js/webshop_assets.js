(function () {
	var CACHE_KEY = "ws_assets";
	var CACHE_TTL = 5 * 60 * 1000; // 5 minutes

	function applyAssets(assets) {
		document.querySelectorAll("[data-ws-image]").forEach(function (el) {
			var key = el.getAttribute("data-ws-image");
			if (assets[key]) {
				if (el.tagName === "IMG") {
					el.src = assets[key];
				} else {
					el.style.backgroundImage = "url('" + assets[key] + "')";
				}
			}
		});
	}

	function loadAssets() {
		try {
			var cached = sessionStorage.getItem(CACHE_KEY);
			if (cached) {
				var entry = JSON.parse(cached);
				if (Date.now() - entry.ts < CACHE_TTL) {
					applyAssets(entry.data);
					return;
				}
			}
		} catch (e) {}

		fetch("/api/method/invento_webshop.api.webshop_settings.get_webshop_assets")
			.then(function (r) { return r.json(); })
			.then(function (json) {
				var assets = json.message || {};
				try {
					sessionStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), data: assets }));
				} catch (e) {}
				applyAssets(assets);
			})
			.catch(function () {});
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", loadAssets);
	} else {
		loadAssets();
	}
})();
