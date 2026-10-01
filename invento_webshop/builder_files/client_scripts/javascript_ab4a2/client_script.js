/* ================= HELPER FUNCTIONS ================= */
function updateURLParam(key, value, isArray = false, reload = true) {
  const params = new URLSearchParams(window.location.search);
  if (isArray) {
    params.delete(key + '[]');
    if (Array.isArray(value) && value.length > 0) {
      value.forEach(v => params.append(key + '[]', v));
    }
  } else {
    if (value === null || value === '') {
      params.delete(key);
    } else {
      params.set(key, value);
    }
  }
  const newUrl = `${window.location.pathname}?${params.toString()}`;
  if (reload) {
    window.location.href = newUrl;
  } else {
    window.history.replaceState({}, "", newUrl);
  }
}

function getURLParams(key, isArray = false) {
  const params = new URLSearchParams(window.location.search);
  return isArray ? params.getAll(key + '[]') : params.get(key);
}

/* ================= CATEGORY FILTER ================= */
document.querySelectorAll('#category-filters .category-item').forEach(item => {
  item.addEventListener('click', () => {
    const name = item.dataset.name;
    updateURLParam('category_name', name);
    document.querySelectorAll('#category-filters .category-item').forEach(i => i.classList.remove('active'));
    item.classList.add('active');
  });
});

document.querySelectorAll('#page-length-filter button').forEach(btn => {
  btn.addEventListener('click', () => {
    const length = btn.dataset.pageLength;
    updateURLParam('page_length', length);
  });
});

/* ================= PRICE FILTER ================= */
const priceInput = document.getElementById('price-range');
const priceText = document.getElementById('price-text');
const priceBtn = document.getElementById('price-apply-btn');

priceInput.addEventListener('input', () => {
  const min = priceInput.min;
  const max = priceInput.value;
  priceText.textContent = `£${min} — £${max}`;
});

priceBtn.addEventListener('click', () => {
  const min = priceInput.min;
  const max = priceInput.value;
  updateURLParam('price_start', min);
  updateURLParam('price_end', max);
});

/* ================= STOCK FILTER ================= */
document.querySelectorAll('#stock-filters input[type="checkbox"]').forEach(cb => {
  cb.addEventListener('change', () => {
    let stocks = getURLParams('stock', true);
    if (cb.checked) {
      if (!stocks.includes(cb.value)) stocks.push(cb.value);
    } else {
      stocks = stocks.filter(s => s !== cb.value);
    }
    updateURLParam('stock', stocks, true);
  });
});

/* ================= WEIGHT FILTER ================= */
document.querySelectorAll('#weight-filters input[type="checkbox"]').forEach(cb => {
  cb.addEventListener('change', () => {
    let weights = getURLParams('weight', true);
    if (cb.checked) {
      if (!weights.includes(cb.value)) weights.push(cb.value);
    } else {
      weights = weights.filter(w => w !== cb.value);
    }
    updateURLParam('weight', weights, true);
  });
});

/* ================= SHOW MORE ================= */

window._cardTemplate = null;
window._itemsGrid = null;

window.showMoreState = {
  offset: 0,
  limit: 20,
  loading: false,
  hasMore: true,
};

window.getItemsGrid = function() {
  if (window._itemsGrid) return window._itemsGrid;
  const btn = document.querySelector('.show_more_btn');
  if (!btn) return null;
  const grid = btn.closest('div')?.previousElementSibling;
  if (!grid) return null;
  window._itemsGrid = grid;
  return window._itemsGrid;
};

window.getCardTemplate = function() {
  if (window._cardTemplate) return window._cardTemplate;
  const grid = window.getItemsGrid();
  const firstCard = grid?.querySelector('.product-card') || document.querySelector('.product-card');
  if (!firstCard) {
    console.warn('[ShowMore] No .product-card found');
    return null;
  }
  window._cardTemplate = firstCard.cloneNode(true);
  console.log('[ShowMore] Card template cached:', window._cardTemplate.className);
  return window._cardTemplate;
};

window.getShowMoreFilters = function() {
  return {
    price_start: getURLParams('price_start') || 0,
    price_end: getURLParams('price_end') || 0,
    category_name: getURLParams('category_name') || null,
    page_length: getURLParams('page_length') || 20,
    stock: getURLParams('stock', true),
    weight: getURLParams('weight', true),
  };
};

window.buildVariantForm = function(attributes) {
  let html = `<form id="variant-form" class="variant-form">`;
  attributes.forEach(attr => {
    html += `<div class="variant-group">
      <p class="variant-label">${attr.attribute}</p>
      <div class="variant-options" data-attribute="${attr.attribute}">
        ${attr.values.map(val => {
          const priceHtml = val.price && val.price > 0
            ? `<span class="variant-price"> (${val.formatted_price})</span>` : '';
          return `<label class="variant-option">
            <input type="radio" name="${attr.attribute}" value="${val.value}" />
            <span class="variant-pill">
              <span class="variant-text">${val.value}</span>${priceHtml}
            </span>
          </label>`;
        }).join('')}
      </div>
    </div>`;
  });
  html += `</form>`;
  return html;
};

window._addToCart = function(itemCode, qty) {
  const user_id = frappe.get_cookie('user_id');
  if (!user_id || user_id === 'Guest') {
    Toastify({
      text: 'Please login to add items to your cart.',
      close: true, gravity: 'top', position: 'center', stopOnFocus: true,
      style: { background: 'linear-gradient(to right, #ff416c, #ff4b2b)' }
    }).showToast();
    setTimeout(() => { window.location.href = '/login'; }, 1000);
    return;
  }

  const HEADERS = {
    'Content-Type': 'application/json',
    'x-frappe-csrf-token': frappe.csrf_token,
    'x-requested-with': 'XMLHttpRequest',
    'Accept': 'application/json, text/javascript, */*; q=0.01'
  };

  fetch('/api/method/invento_webshop.webshop_functions.cart.update_cart', {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify({
      item_code: itemCode,
      qty: qty,
      cart_items: frappe.get_cookie('cart_items')
    }),
  })
    .then(r => {
      if (!r.ok) return r.json().then(e => { throw e; });
      return r.json();
    })
    .then(() => {
      const cartCount = frappe.get_cookie('cart_count') || 0;
      const cartCountEl = document.getElementById('cart_count');
      if (cartCountEl) cartCountEl.innerText = cartCount;
      Toastify({
        text: 'Item added to cart!',
        close: true, gravity: 'top', position: 'center', stopOnFocus: true,
        style: { background: 'var(--primary-color)' }
      }).showToast();
    })
    .catch(err => {
      Toastify({
        text: err.message || 'Failed to add item to cart',
        close: true, gravity: 'top', position: 'center', stopOnFocus: true,
        style: { background: 'var(--primary-color-light)' }
      }).showToast();
    });
};

window.buildItemCard = function(item) {
  const template = window.getCardTemplate();
  if (!template) {
    console.warn('[ShowMore] No card template available');
    return null;
  }

  const card = template.cloneNode(true);
  const route = '/' + (item.custom_route || '#').replace(/^\//, '');

  const HEADERS = {
    'Content-Type': 'application/json',
    'x-frappe-csrf-token': frappe.csrf_token,
    'x-requested-with': 'XMLHttpRequest',
    'Accept': 'application/json, text/javascript, */*; q=0.01'
  };

const NO_IMAGE = '/files/no_image_10e2dfc9.webp';

// Image link
const imageLink = card.querySelector('a.product-image');
if (imageLink) {
  imageLink.href = route;
  const templateImgLink = template.querySelector('a.product-image');
  if (templateImgLink) {
    const h = templateImgLink.getBoundingClientRect().height;
    if (h > 0) {
      imageLink.style.height = h + 'px';
      imageLink.style.overflow = 'hidden';
    }
  }
}

// Image
const img = card.querySelector('img');
if (img) {
  let imgSrc = item.image || item.item_image || '';
  if (imgSrc && !imgSrc.startsWith('/') && !imgSrc.startsWith('http')) {
    imgSrc = '/files/' + imgSrc;
  }
  img.src = imgSrc || NO_IMAGE;
  img.alt = item.item_name || '';
  img.onerror = function() {
    this.onerror = null;
    this.src = NO_IMAGE;
    this.style.border = '1px solid #ddd';
  };
}

  // Title link
  const titleLink = card.querySelector('.product-content > a');
  if (titleLink) titleLink.href = route;

  // Title text
  const titleEl = card.querySelector('.product-title');
  if (titleEl) titleEl.textContent = item.item_name || '';

  // Item group + price
  const priceEls = card.querySelectorAll('.product-price');
  if (priceEls[0]) priceEls[0].textContent = item.item_group || '';
  if (priceEls[1]) {
    if (item.formatted_price && item.formatted_price != 0) {
      priceEls[1].textContent = item.formatted_price;
      priceEls[1].style.display = '';
    } else {
      priceEls[1].style.display = 'none';
    }
  }

  // CTA button
  const btn = card.querySelector('button');
  if (btn) {
    btn.setAttribute('data-item_code', item.item_code);
    const btnText = btn.querySelector('p') || btn.querySelector('div');

    if (item.has_variants == 1) {
      btn.classList.remove('add-to-cart-btn');
      btn.classList.add('solid-button', 'add-variants-cart'); btn._listenerBound = true;
      if (btnText) btnText.textContent = 'Explore Variants';

      btn.addEventListener('click', function() { window._exploreVariants(this); });

    } else {
      btn.classList.remove('add-variants-cart');
      btn.classList.add('solid-button', 'add-to-cart-btn'); btn._listenerBound = true;
      if (btnText) btnText.textContent = 'Add to Cart';

      btn.addEventListener('click', function() {
        window._addToCart(item.item_code, 1);
      });
    }
  }
if (btn) {
  const btnParent = btn.closest('div');
  if (btnParent) btnParent.style.marginBottom = item.has_variants == 1 ? '0' : '-20px';
}
  return card;
};

window.renderItems = function(items) {
  const grid = window.getItemsGrid();
  if (!grid) {
    console.warn('[ShowMore] Could not find items grid');
    return;
  }

  items.forEach(item => {
    const card = window.buildItemCard(item);
    if (!card) {
      console.warn('[ShowMore] Card build failed for item:', item.item_name);
      return;
    }

    card.style.opacity = '0';
    card.style.transform = 'translateY(10px)';
    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    grid.appendChild(card);

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      });
    });
  });
};

window.fetchMoreItems = async function() {
  if (window.showMoreState.loading || !window.showMoreState.hasMore) return;

  window.showMoreState.loading = true;
  const btn = document.querySelector('.show_more_btn');
  if (btn) {
    btn.style.opacity = '0.5';
    btn.style.pointerEvents = 'none';
  }

  const filters = window.getShowMoreFilters();

  try {
    const response = await fetch('/api/method/invento_webshop.api.item.load_more_items', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': frappe?.csrf_token || '',
      },
      body: JSON.stringify({
        filters: filters,
        offset: window.showMoreState.offset,
        limit: window.showMoreState.limit,
      }),
    });

    const data = await response.json();
    const result = data.message;

    if (!result || !result.items || result.items.length === 0) {
      window.showMoreState.hasMore = false;
      if (btn) btn.style.display = 'none';
      return;
    }

    window.renderItems(result.items);
    window.showMoreState.offset += result.items.length;

    if (
      result.items.length === 0 ||
      result.items.length < window.showMoreState.limit ||
      window.showMoreState.offset >= result.items_count
    ) {
      window.showMoreState.hasMore = false;
      if (btn) btn.style.display = 'none';
    }

  } catch (err) {
    console.error('[ShowMore] Fetch failed:', err);
  } finally {
    window.showMoreState.loading = false;
    if (btn) {
      btn.style.opacity = '1';
      btn.style.pointerEvents = 'auto';
    }
  }
};

/* ================= RESTORE FILTERS + INIT ================= */
window.addEventListener('DOMContentLoaded', () => {
  // Restore category
  const cat = getURLParams('category_name');
  if (cat) {
    const el = document.querySelector(`#category-filters .category-item[data-name="${cat}"]`);
    if (el) el.classList.add('active');
  }

  // Restore price
  const priceStart = getURLParams('price_start');
  const priceEnd = getURLParams('price_end');
  if (priceStart && priceEnd) {
    priceInput.value = priceEnd;
    priceText.textContent = `£${priceStart} — £${priceEnd}`;
  }

  // Restore stock
  const stocks = getURLParams('stock', true);
  stocks.forEach(s => {
    const cb = document.querySelector(`#stock-filters input[value="${s}"]`);
    if (cb) cb.checked = true;
  });

  // Restore weights
  const weights = getURLParams('weight', true);
  weights.forEach(w => {
    const cb = document.querySelector(`#weight-filters input[value="${w}"]`);
    if (cb) cb.checked = true;
  });

  const pageLength = getURLParams('page_length');
  if (pageLength) {
    document.querySelectorAll('#page-length-filter button').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.pageLength === pageLength);
    });
  }

  // Show more init
  const grid = window.getItemsGrid();
  if (grid) {
    window.showMoreState.offset = grid.children.length;
    console.log(`[ShowMore] Initialized with offset: ${window.showMoreState.offset}`);
  }

  window.getCardTemplate();

  const showMoreBtn = document.querySelector('.show_more_btn');
  if (showMoreBtn) {
    showMoreBtn.addEventListener('click', (e) => {
      e.preventDefault();
      window.fetchMoreItems();
    });
  } else {
    console.warn('[ShowMore] Button not found');
  }
});

/* ======================================================
   VARIANT MODAL — fully self-contained, inline styles.
   All colors resolved from computed CSS vars at click-time.
   ====================================================== */

window.closeCustomModal = function() {
  var el = document.getElementById('invento-custom-modal');
  if (el) el.parentNode.removeChild(el);
};

/* buildVariantForm(attributes, C)  –  C = computed theme colours */
window.buildVariantForm = function(attrs, C) {
  var primary     = (C && C.primary)      || '#333';
  var faint       = (C && C.primaryFaint) || '#eee';
  var textColor   = (C && C.primaryText)  || '#222';

  var html = '<form id="variant-form" style="margin:0;padding:0">';
  attrs.forEach(function(attr) {
    html += '<div style="margin-bottom:18px">'
      + '<p style="font-size:13px;font-weight:600;color:' + textColor
      + ';margin:0 0 8px 0">' + attr.attribute + '</p>'
      + '<div data-attribute="' + attr.attribute
      + '" style="display:flex;flex-wrap:wrap;gap:8px">';

    attr.values.forEach(function(val) {
      var price = (val.price && val.price > 0 && val.formatted_price)
        ? ' <span class="_pprice" style="color:' + primary
          + ';font-size:11px;font-style:italic">(' + val.formatted_price + ')</span>'
        : '';
      html += '<label style="cursor:pointer">'
        + '<input type="radio" name="' + attr.attribute
        + '" value="' + val.value + '" style="display:none">'
        + '<span class="_vpill" style="'
        + 'display:inline-flex;align-items:center;gap:4px;'
        + 'padding:7px 16px;border:1.5px solid ' + faint + ';border-radius:20px;'
        + 'font-size:13px;color:' + textColor + ';background:#fff;'
        + 'transition:all .15s;cursor:pointer;user-select:none">'
        + val.value + price + '</span></label>';
    });
    html += '</div></div>';
  });
  html += '</form>';
  return html;
};

/* openCustomModal({title, body, footer}, C) */
window.openCustomModal = function(opts, C) {
  window.closeCustomModal();

  var primary   = (C && C.primary)     || '#333';
  var btnColor  = (C && C.btnColor)    || '#fff';
  var faint     = (C && C.primaryFaint)|| '#eee';
  var textColor = (C && C.primaryText) || '#222';

  var footerHtml = opts.footer
    ? '<div style="padding:12px 20px;border-top:1px solid ' + faint + ';'
      + 'display:flex;gap:10px;justify-content:flex-end;background:#fafafa">'
      + opts.footer + '</div>'
    : '';

  var overlay = document.createElement('div');
  overlay.id = 'invento-custom-modal';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.45);'
    + 'z-index:99999;display:flex;align-items:center;justify-content:center';

  overlay.innerHTML =
    '<div style="background:#fff;border-radius:10px;min-width:300px;max-width:500px;'
    + 'width:92%;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.2)">'
    /* Header — use primary-color as accent background */
    + '<div style="background:' + primary + ';color:' + btnColor + ';'
    + 'padding:16px 20px;font-size:16px;font-weight:600;'
    + 'display:flex;justify-content:space-between;align-items:center">'
    + '<span>' + (opts.title || '') + '</span>'
    + '<button id="ivt-close" type="button" style="cursor:pointer;background:none;'
    + 'border:none;color:' + btnColor + ';font-size:22px;line-height:1;padding:0">'
    + '&#x2715;</button></div>'
    /* Body */
    + '<div style="padding:20px;max-height:60vh;overflow-y:auto">'
    + (opts.body || '') + '</div>'
    + footerHtml + '</div>';

  /* Highlight selected pill within its own group only */
  overlay.addEventListener('change', function(e) {
    if (e.target.type !== 'radio') return;
    var group = e.target.closest('[data-attribute]');
    if (!group) return;
    /* Reset all pills in this group */
    group.querySelectorAll('._vpill').forEach(function(pill) {
      pill.style.background  = '#fff';
      pill.style.color       = textColor;
      pill.style.borderColor = faint;
      var pp = pill.querySelector('._pprice');
      if (pp) pp.style.color = primary;
    });
    /* Highlight selected pill */
    var sel = e.target.nextElementSibling;
    if (sel && sel.classList.contains('_vpill')) {
      sel.style.background  = primary;
      sel.style.color       = btnColor;
      sel.style.borderColor = primary;
      var pp = sel.querySelector('._pprice');
      if (pp) pp.style.color = btnColor;
    }
  });

  overlay.querySelector('#ivt-close').onclick = window.closeCustomModal;
  overlay.onclick = function(e) { if (e.target === overlay) window.closeCustomModal(); };
  document.body.appendChild(overlay);
};

window._exploreVariants = function(btn) {
  var itemCode = btn.getAttribute('data-item_code');
  if (!itemCode) return;

  /* Read actual computed theme colours from :root */
  var rs = getComputedStyle(document.documentElement);
  var C = {
    primary:      rs.getPropertyValue('--primary-color').trim()       || '#333',
    primaryFaint: rs.getPropertyValue('--primary-color-faint').trim() || '#eee',
    primaryText:  rs.getPropertyValue('--primary-text-color').trim()  || '#222',
    btnBg:        rs.getPropertyValue('--btn-bg').trim()              || '#333',
    btnColor:     rs.getPropertyValue('--btn-color').trim()           || '#fff',
  };

  var H = {
    'Content-Type': 'application/json',
    'x-frappe-csrf-token': (frappe && frappe.csrf_token) || '',
    'x-requested-with': 'XMLHttpRequest'
  };
  var BS = 'cursor:pointer;padding:9px 22px;border-radius:6px;font-size:14px;'
         + 'font-weight:500;border:none;transition:all .2s';

  fetch('/api/method/invento_webshop.webshop_functions.variant_selector.utils'
    + '.get_attributes_and_values?item_code=' + encodeURIComponent(itemCode),
    { method: 'GET', headers: H })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (!data.message || !data.message.length) {
      Toastify({ text: 'No variants available.', close: true,
        gravity: 'top', position: 'center', stopOnFocus: true,
        style: { background: C.primary } }).showToast();
      return;
    }

    var footer =
      '<button type="button" id="ivt-cancel" style="' + BS
      + ';background:#f5f5f5;color:' + C.primaryText + '">Cancel</button>'
      + '<button type="button" id="ivt-add" style="' + BS
      + ';background:' + C.primary + ';color:' + C.btnColor + '">Add to Cart</button>';

    window.openCustomModal({
      title:  'Select Variant',
      body:   window.buildVariantForm(data.message, C),
      footer: footer
    }, C);

    document.getElementById('ivt-cancel').onclick = window.closeCustomModal;
    document.getElementById('ivt-add').onclick = function() {
      var form = document.getElementById('variant-form');
      var ok = true;
      form.querySelectorAll('[data-attribute]').forEach(function(g) {
        var a = g.getAttribute('data-attribute');
        if (!form.querySelector('input[name="' + a + '"]:checked')) {
          ok = false;
          g.querySelectorAll('._vpill').forEach(function(p) {
            p.style.borderColor = C.primary;
            p.style.outline     = '1px solid ' + C.primary;
          });
        }
      });
      if (!ok) {
        Toastify({ text: 'Please select all options.', close: true,
          gravity: 'top', position: 'center', stopOnFocus: true,
          style: { background: C.primary } }).showToast();
        return;
      }
      var sel = Object.fromEntries(new FormData(form).entries());
      fetch('/api/method/invento_webshop.webshop_functions.variant_selector.utils'
        + '.get_next_attribute_and_values',
        { method: 'POST', headers: H,
          body: JSON.stringify({ item_code: itemCode, selected_attributes: sel }) })
      .then(function(r) { return r.json(); })
      .then(function(res) { window._addToCart(res.message, 1); });
      window.closeCustomModal();
    };
  })
  .catch(function(err) {
    console.error('[Variant]', err);
    Toastify({ text: 'Failed to load variants.', close: true,
      gravity: 'top', position: 'center', stopOnFocus: true,
      style: { background: C.primary } }).showToast();
  });
};
