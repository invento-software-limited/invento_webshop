// Copyright (c) 2026, Invento Software Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Webshop Theme", {
	setup(frm) {
		frm.get_field("sample").html(THEME_HELP_HTML);
	},

	refresh(frm) {
		const is_applied = frm.doc.status === "Applied";

		if (!frm.is_new()) {
			if (is_applied) {
				frm.set_intro(__("This theme is currently active on the webshop."), "green");
			}

			frm.add_custom_button(
				is_applied ? __("Applied ✓") : __("Apply Theme"),
				function () {
					if (is_applied) return;
					frappe.confirm(
						__("Apply <b>{0}</b> to the webshop? This will update Webshop Settings, regenerate assets and clear all caches.", [frm.doc.theme_name]),
						function () {
							frappe.call({
								method: "invento_webshop.invento_webshop.doctype.webshop_theme.webshop_theme.apply_theme",
								args: { name: frm.doc.name },
								freeze: true,
								freeze_message: __("Applying theme — regenerating assets and clearing cache…"),
								callback: function (r) {
									if (!r.exc) {
										frappe.show_alert({ message: __("Theme applied successfully"), indicator: "green" });
										frm.reload_doc();
									}
								},
							});
						}
					);
				},
				is_applied ? "success" : "primary"
			);
		}
	},
});

const THEME_HELP_HTML = `
<style>
  .theme-help { font-family: inherit; color: var(--text-color, #333); line-height: 1.6; }
  .theme-help h3 { font-size: 15px; font-weight: 700; margin: 20px 0 8px; color: var(--text-color, #222); border-bottom: 1px solid var(--border-color, #e0e0e0); padding-bottom: 6px; }
  .theme-help h3:first-child { margin-top: 0; }
  .theme-help p { margin: 6px 0 10px; font-size: 13px; }
  .theme-help ul, .theme-help ol { margin: 6px 0 10px; padding-left: 20px; font-size: 13px; }
  .theme-help li { margin-bottom: 4px; }
  .theme-help .step-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 12px 0; }
  .theme-help .step-card { background: var(--control-bg, #f8f8f8); border: 1px solid var(--border-color, #e0e0e0); border-radius: 8px; padding: 14px 16px; }
  .theme-help .step-num { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: var(--primary, #4c72ed); color: #fff; border-radius: 50%; font-size: 12px; font-weight: 700; margin-bottom: 8px; }
  .theme-help .step-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
  .theme-help .step-desc { font-size: 12px; color: var(--text-muted, #888); }
  .theme-help .affects-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px; margin: 10px 0; }
  .theme-help .affect-item { background: var(--control-bg, #f8f8f8); border-left: 3px solid var(--primary, #4c72ed); padding: 8px 12px; border-radius: 0 4px 4px 0; font-size: 12px; }
  .theme-help .affect-item strong { display: block; font-size: 12px; margin-bottom: 2px; }
  .theme-help .var-table { width: 100%; border-collapse: collapse; font-size: 12px; margin: 10px 0; }
  .theme-help .var-table th { text-align: left; padding: 6px 10px; background: var(--control-bg, #f0f0f0); border: 1px solid var(--border-color, #ddd); font-weight: 600; }
  .theme-help .var-table td { padding: 5px 10px; border: 1px solid var(--border-color, #ddd); vertical-align: top; }
  .theme-help .var-table tr:nth-child(even) td { background: var(--control-bg, #fafafa); }
  .theme-help .note { background: #fffbe6; border: 1px solid #ffe58f; border-radius: 6px; padding: 10px 14px; font-size: 12px; margin: 10px 0; }
  .theme-help .note strong { color: #d48806; }
  .theme-help code { background: var(--control-bg, #f0f0f0); padding: 1px 5px; border-radius: 3px; font-family: monospace; font-size: 11px; }
</style>

<div class="theme-help">

  <h3>Quick Start — 3 Steps</h3>
  <div class="step-grid">
    <div class="step-card">
      <div class="step-num">1</div>
      <div class="step-title">Pick your colors</div>
      <div class="step-desc">Fill in the <b>Quick Setup</b> section (3 colors). They auto-generate all shades. Optionally override Button Colors.</div>
    </div>
    <div class="step-card">
      <div class="step-num">2</div>
      <div class="step-title">Add images</div>
      <div class="step-desc">Upload <b>Carousel Images</b> for the homepage slider. Logos and SVG backgrounds are auto-generated.</div>
    </div>
    <div class="step-card">
      <div class="step-num">3</div>
      <div class="step-title">Apply Theme</div>
      <div class="step-desc">Click the <b>Apply Theme</b> button (top-right). The webshop updates instantly — no restart needed.</div>
    </div>
  </div>

  <div class="note">
    <strong>Tip:</strong> Only one theme can be <b>Applied</b> at a time. Applying a new theme automatically deactivates the previous one. You can have as many saved themes as you like.
  </div>

  <h3>Section Reference</h3>
  <ul>
    <li><b>Quick Setup — Base Colors</b>: Set your primary brand color, main text color and page background. On Apply, all detailed shades in the sections below are auto-calculated. Leave blank to keep current values.</li>
    <li><b>Button Colors</b>: Controls every CTA button on the site — Add to Cart, Contact, Apply, etc. Background + text for default and hover states.</li>
    <li><b>Brand Colors (Advanced)</b>: Fine-tune the four primary shades (normal, dark hover, light hover, faint tint). Auto-filled from Quick Setup but can be overridden.</li>
    <li><b>Text Colors (Advanced)</b>: Primary dark text and its hover / muted variant.</li>
    <li><b>Background Colors (Advanced)</b>: Three background tones used in sections, cards and panels.</li>
    <li><b>Branding Assets</b>: Navbar logo, footer logo and the "What Makes Us Different" background SVG are all auto-generated on Apply. You may also upload custom images.</li>
    <li><b>Hero Carousel</b>: Up to 3 banner images for the homepage slider. Recommended 1280 × 480 px.</li>
    <li><b>Custom Images</b>: Any additional assets your pages reference.</li>
  </ul>

  <h3>Where the Theme Takes Effect</h3>
  <div class="affects-grid">
    <div class="affect-item"><strong>Navbar</strong>Logo, navigation links, cart icon</div>
    <div class="affect-item"><strong>Hero Carousel</strong>Banner images and slide overlays</div>
    <div class="affect-item"><strong>Buttons (all pages)</strong>Add to Cart, Contact, Apply, Explore Variants, Show More</div>
    <div class="affect-item"><strong>Product Cards</strong>Prices, titles, hover borders</div>
    <div class="affect-item"><strong>Variant Modal</strong>Header, selected option pill, Add to Cart button</div>
    <div class="affect-item"><strong>Filter Panel (Shop)</strong>Checkbox accents, active filter badges</div>
    <div class="affect-item"><strong>Get in Touch Section</strong>Background tint, Contact button</div>
    <div class="affect-item"><strong>Opening Hours Section</strong>Background SVG sunrise illustration</div>
    <div class="affect-item"><strong>"What Makes Us Different"</strong>Icon accent, section background SVG</div>
    <div class="affect-item"><strong>Footer</strong>Logo, background color, text colors</div>
    <div class="affect-item"><strong>Forms (Address, Checkout)</strong>Input borders, step buttons, submit buttons</div>
    <div class="affect-item"><strong>Toast / Alert Messages</strong>Background accent on success / info toasts</div>
  </div>

  <h3>CSS Variables Generated on Apply</h3>
  <p>These variables are injected into every page via <code>/ws-colors</code> and can be used in custom CSS with <code>var(--variable-name)</code>.</p>
  <table class="var-table">
    <thead>
      <tr><th>Variable</th><th>Source field</th><th>Used for</th></tr>
    </thead>
    <tbody>
      <tr><td><code>--primary-color</code></td><td>Primary Color</td><td>Accent borders, badges, icon fills</td></tr>
      <tr><td><code>--primary-color-hover</code></td><td>Primary Dark (Hover)</td><td>Pressed/active accent states</td></tr>
      <tr><td><code>--primary-color-light</code></td><td>Primary Light (Hover)</td><td>Hover tints, underlines</td></tr>
      <tr><td><code>--primary-color-faint</code></td><td>Primary Faint</td><td>Section background tints, pill borders</td></tr>
      <tr><td><code>--primary-color-faint-deep</code></td><td>Auto-derived (+20% depth)</td><td>Deeper tint for "Get in Touch" bg</td></tr>
      <tr><td><code>--btn-bg</code></td><td>Button Background</td><td>All button fills</td></tr>
      <tr><td><code>--btn-color</code></td><td>Button Text</td><td>All button labels</td></tr>
      <tr><td><code>--btn-hover-bg</code></td><td>Button Hover Background</td><td>Button fill on hover</td></tr>
      <tr><td><code>--btn-anim-color</code></td><td>Auto-derived (complementary hue)</td><td>Button shimmer animation</td></tr>
      <tr><td><code>--primary-text-color</code></td><td>Primary Text</td><td>Headings, prices, product titles</td></tr>
      <tr><td><code>--primary-text-hover</code></td><td>Text Hover / Muted</td><td>Subtitles, secondary labels</td></tr>
      <tr><td><code>--light-bg-color</code></td><td>Light Background</td><td>Alternating section backgrounds</td></tr>
      <tr><td><code>--warm-bg-color</code></td><td>Warm Background</td><td>Product grid, card backgrounds</td></tr>
      <tr><td><code>--secondary-bg-color</code></td><td>Secondary Background</td><td>Footer, filter panels, input fields</td></tr>
    </tbody>
  </table>

  <div class="note">
    <strong>Cache note:</strong> After applying a theme, do a hard-refresh in the browser (<code>Ctrl+Shift+R</code> / <code>Cmd+Shift+R</code>) to see updated colors. Frappe clears server caches automatically on Apply.
  </div>

</div>
`;
