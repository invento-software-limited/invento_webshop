const desktopOnly = window.matchMedia("(min-width: 1024px)");

function initProcessAnimation() {
  if (!desktopOnly.matches) return;

  document.addEventListener("scroll", onScroll);
}

function onScroll() {
  const section = document.querySelector(".process-section");
  if (!section) return;

  const rect = section.getBoundingClientRect();
  const vh = window.innerHeight;

  const START_OFFSET = vh * 0.9;
  const END_OFFSET   = rect.height * 0.7;

  let progress = (START_OFFSET - rect.top) / END_OFFSET;
  progress = Math.min(Math.max(progress, 0), 1);

  animate(progress);
}

// -------- helpers ----------
function lerp(a, b, t) {
  return a + (b - a) * t;
}

function clamp(v) {
  return Math.min(Math.max(v, 0), 1);
}

function move(selector, p, index, xStart, xEnd) {
  const el = document.querySelector(selector);
  if (!el) return;

  const Y_START = 0;
  const Y_END = 0.7;
  const CARD_COUNT = 4;
  const SLICE = (Y_END - Y_START) / CARD_COUNT;

  let x = xStart;
  let y = 250;

  const yStart = Y_START + index * SLICE + 0.02 * index;

  if (p < Y_END) {
    let tY = clamp((p - yStart) / SLICE);
    y = lerp(250, 0, tY);
  } else {
    y = 0;
    let tX = clamp((p - Y_END) / (1 - Y_END));
    x = lerp(xStart, xEnd, tX);
  }

  el.style.transform = `translate(${x}%, ${y}%)`;
}

function animate(p) {
  move(".process-card-one",   p, 0,  160,  0);
  move(".process-card-two",   p, 1,   52,  0);
  move(".process-card-three", p, 2,  -56,  0);
  move(".process-card-four",  p, 3, -163,  0);
}

initProcessAnimation();


document.querySelectorAll('.slider').forEach(slider => {
    const slidesWrapper = slider.querySelector('.slider-images');
    const slides = slider.querySelectorAll('.slide');
    const indicators = slider.querySelectorAll('.indicator');

    if (!slidesWrapper || slides.length === 0) return;

    let currentIndex = 0;
    const totalSlides = slides.length;

    // Clone first slide for infinite loop
    const firstSlideClone = slides[0].cloneNode(true);
    slidesWrapper.appendChild(firstSlideClone);

    // Function to show slide
    function showSlide(index) {
        // ✅ Slower and smoother transition
        slidesWrapper.style.transition = 'transform 1.5s ease-in-out';
        slidesWrapper.style.transform = `translateX(-${index * 100}%)`;

        // Update indicators
        if (indicators.length > 0) {
            let indicatorIndex = index === totalSlides ? 0 : index;
            indicators.forEach((indicator, i) => {
                indicator.classList.toggle('active', i === indicatorIndex);
            });
        }
    }

    // Indicator clicks
    if (indicators.length > 0) {
        indicators.forEach((indicator, i) => {
            indicator.addEventListener('click', () => {
                currentIndex = i;
                showSlide(currentIndex);
            });
        });
    }

    // Auto-slide
    setInterval(() => {
        currentIndex++;
        showSlide(currentIndex);

        // Reset to first slide for infinite loop
        if (currentIndex === totalSlides) {
            setTimeout(() => {
                slidesWrapper.style.transition = 'none';
                currentIndex = 0;
                slidesWrapper.style.transform = `translateX(0)`;
            }, 1500); // match transition duration
        }
    }, 4000); // time between slides (can increase for slower effect)
});

document.addEventListener('DOMContentLoaded', function() {
    // 1. Load Swiper CSS
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css';
    document.head.appendChild(link);
    // 2. Load Swiper JS
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js';
    script.onload = initSliders;
    document.head.appendChild(script);
    function initSliders() {
        // Configuration for each slider type
        const sliderConfigs = [
            { selector: '[id="flashsale"]', slidesPerView: { 640: 2, 768: 3, 1024: 5 } },
            { selector: '[id="review"]', slidesPerView: { 640: 1, 768: 2, 1024: 2.5 } },
            { selector: '[id="blog"]', slidesPerView: { 640: 1, 768: 2, 1024: 3 } }
        ];
        sliderConfigs.forEach(config => {
            // Use querySelectorAll to find ALL blocks with the matching ID
            // This handles cases where IDs might be duplicated in the builder
            const containers = document.querySelectorAll(config.selector);
            
            containers.forEach(container => {
                // Initialize slider if it hasn't been initialized yet
                if (!container.classList.contains('swiper-initialized')) {
                    initSingleSlider(container, config);
                }
            });
        });
    }
    function initSingleSlider(container, config) {
        // Check if the container has children to slide
        if (container.children.length === 0) {
            return;
        }
        // 4. Prepare the DOM for Swiper
        container.classList.add('swiper');
        
        // Reset styles that might interfere with Swiper
        container.style.display = 'block';
        container.style.gridTemplateColumns = 'none';
        container.style.gap = '0';
        container.style.overflow = 'hidden'; // Important for Swiper
        // Create wrapper
        const wrapper = document.createElement('div');
        wrapper.classList.add('swiper-wrapper');
        // Move all children (slides) into the wrapper
        while (container.firstChild) {
            const child = container.firstChild;
            // Ensure child is an element node
            if (child.nodeType === 1) {
                child.classList.add('swiper-slide');
                // Reset child styles if necessary
                child.style.height = 'auto'; 
                child.style.width = 'auto'; // Let Swiper handle width
            }
            wrapper.appendChild(child);
        }
        container.appendChild(wrapper);
        // 5. Initialize Swiper
        new Swiper(container, {
            slidesPerView: 1,
            spaceBetween: 20,
            speed: 1600,
            loop: true,
            autoplay: {
                delay: 4200,
                disableOnInteraction: false,
            },
            breakpoints: {
                640: {
                    slidesPerView: config.slidesPerView[640],
                    spaceBetween: 20,
                },
                768: {
                    slidesPerView: config.slidesPerView[768],
                    spaceBetween: 30,
                },
                1024: {
                    slidesPerView: config.slidesPerView[1024],
                    spaceBetween: 30,
                },
            },
            navigation: {
              nextEl: '.swiper-next',
              prevEl: '.swiper-prev',
            },
        });
    }
});

(() => {
  const wrapper = document.querySelector(".parallax-wrapper");
  const images = document.querySelectorAll(".parallax-image");
  const vh = window.innerHeight;

  window.addEventListener("scroll", () => {
    const rect = wrapper.getBoundingClientRect();
    const totalScroll = vh * images.length;

    const scrolled = Math.min(
      Math.max(vh - rect.top, 0),
      totalScroll
    );

    const index = Math.floor(scrolled / (vh + 80));

    images.forEach((img, i) => {
      img.classList.toggle("is-active", i === index);
    });
  });
})();