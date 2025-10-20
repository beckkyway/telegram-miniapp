const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// === Автообновление Mini App при новой версии ===
(async () => {
  try {
    // Загружаем текущую версию с сервера
    const res = await fetch('/version.txt', { cache: 'no-store' });
    if (!res.ok) return;
    const serverVersion = (await res.text()).trim();

    // Проверяем, что у нас в localStorage
    const localVersion = localStorage.getItem('frontend_version');

    // Если версия изменилась → обновляем страницу
    if (localVersion && localVersion !== serverVersion) {
      console.log('🔄 Новая версия фронтенда. Перезагружаем Mini App...');
      localStorage.setItem('frontend_version', serverVersion);
      location.reload(true);
    } else {
      localStorage.setItem('frontend_version', serverVersion);
    }
  } catch (err) {
    console.warn('⚠️ Ошибка проверки версии:', err);
  }
})();


let currentProduct = null;
let selectedSize = null;
let cart = [];
let allProducts = [];
let pageHistory = ['home'];

// ========== ЛОКАЛЬНОЕ ХРАНИЛИЩЕ ==========
function loadCart() {
    const savedCart = localStorage.getItem('calistor_cart');
    if (savedCart) cart = JSON.parse(savedCart);
    updateCartCount();
}

function saveCart() {
    localStorage.setItem('calistor_cart', JSON.stringify(cart));
    updateCartCount();
}

function updateCartCount() {
    const count = cart.reduce((total, item) => total + item.quantity, 0);
    const cartCountElement = document.getElementById('cart-count');
    const cartButton = document.getElementById('cart-button');

    if (cartCountElement) {
        cartCountElement.textContent = count;
    }

    if (cartButton) {
        if (count > 0) {
            cartButton.classList.add('visible');
        } else {
            cartButton.classList.remove('visible');
        }
    }
}
// Получаем параметры из Telegram WebApp URL
function getQueryParams() {
  const params = new URLSearchParams(window.location.search);
  return Object.fromEntries(params.entries());
}

const query = getQueryParams();
const initialProductId = query.product_id ? parseInt(query.product_id) : null;

document.addEventListener("DOMContentLoaded", () => {
  loadCart();
  loadMainBanner();

  fetch("/api/products")
    .then(res => res.json())
    .then(products => {
      allProducts = products;
      renderProducts(products);

      // 🟢 Если пришёл параметр product_id — сразу открываем этот товар
      if (initialProductId) {
        const product = allProducts.find(p => p.id === initialProductId);
        if (product) showProductDetail(product);
      }
    })
    .catch(err => console.error(err));
});



// ========== НАВИГАЦИЯ ==========
function showPage(pageName) {
  const pages = document.querySelectorAll('.page');
  pages.forEach(page => {
    page.classList.remove('active');
  });

  const targetPage = document.getElementById(`${pageName}-page`);
  if (targetPage) {
    // Добавляем небольшую задержку, чтобы анимация успела отработать
    setTimeout(() => {
      targetPage.classList.add('active');
      window.scrollTo(0, 0); // сбрасываем прокрутку
    }, 50);
  }
}

function goBack() {
    if (pageHistory.length > 1) {
        pageHistory.pop();
        const prev = pageHistory[pageHistory.length - 1];
        showPage(prev);
    } else {
        showPage('home');
    }
}

// ========== ЗАГРУЗКА ТОВАРОВ ==========
document.addEventListener('DOMContentLoaded', function () {
    function loadMainBanner() {
        const bannerImg = document.getElementById('main-banner');
        if (bannerImg) {
            const timestamp = new Date().getTime();
            bannerImg.src = `/static/images/banner.webp?t=${timestamp}`;
            console.log("Баннер загружен с обходом кэша.");
        }
    }

    loadCart();
    loadMainBanner();

    fetch("/api/products")
        .then(res => {
            if (!res.ok) throw new Error('Ошибка загрузки товаров');
            return res.json();
        })
        .then(products => {
            allProducts = products;
            renderProducts(products);
        })
        .catch(error => {
            console.error('Error:', error);
            const productList = document.getElementById("product-list");
            if (productList) {
                productList.innerHTML = '<p>Ошибка загрузки товаров</p>';
            }
        });
});

// ========== ОБРАБОТЧИК РАЗМЕРОВ ==========
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('size-btn')) {
        document.querySelectorAll('.size-btn').forEach(btn => btn.classList.remove('selected'));
        e.target.classList.add('selected');
        selectedSize = e.target.dataset.size;
        const actions = document.querySelector('.product-actions');
        if (actions) {
            actions.classList.add('visible');
        }
    }
});

// ========== РЕНДЕР ТОВАРОВ ==========
function renderProducts(products) {
    const container = document.getElementById("product-list");
    if (!container) return;

    container.innerHTML = products.map(product => {
        const mainImage = product.images && product.images.length > 0
            ? product.images[0]
            : product.image;

        return `
    <div class="product" onclick="openProduct(${product.id})">
        <img src="${mainImage}" alt="${product.name}" onerror="this.src='/static/images/placeholder.webp'" />
        <h3>${product.name}</h3>
        <p>${product.price}₽</p>
    </div>
  `;
    }).join("");

}

// ========== СТРАНИЦА ТОВАРА ==========
function openProduct(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (product) {
        showProductDetail(product);
    }
}

function showProductDetail(product) {
    currentProduct = product;
    selectedSize = null;

    // --- Заполняем текст ---
    document.getElementById('product-title').textContent = product.name;
    document.getElementById('product-price').textContent = product.price;
    document.getElementById('product-color').textContent = product.color;
    document.getElementById('product-composition').textContent = product.composition;
    document.getElementById('product-description-text').textContent = product.description;

    // const actions = document.querySelector('.product-actions');
    // if (actions) actions.classList.remove('visible');


    // --- Размеры ---
    const sizeButtonsContainer = document.getElementById('size-buttons');
    const availableSizes = product.sizes || [];
    if (availableSizes.length > 0) {
        sizeButtonsContainer.innerHTML = availableSizes
            .map(size => `<button class="size-btn" data-size="${size}">${size}</button>`)
            .join('');
    } else {
        sizeButtonsContainer.innerHTML = '<p>Нет доступных размеров</p>';
    }

    // --- Галерея ---
    const galleryImages =
        product.images_large ||
        product.images ||
        [product.image_large || product.image];

    // Безопасная проверка: чтобы не падал при пустых данных
    if (!galleryImages || galleryImages.length === 0) {
        galleryImages = ["/static/images/placeholder.webp"];
    }

    // Передаём изображения в initGallery
    initGallery(galleryImages);

    // --- Переход на страницу товара ---
    showPage('product');
}

// ========== ГАЛЕРЕЯ ==========
function initGallery(images) {
    if (!images || !images.length) return;

    let idx = 0;
    const main = document.getElementById('gallery-main');
    const thumbs = document.getElementById('gallery-thumbs');

    function renderThumbs() {
        thumbs.innerHTML = '';
        images.forEach((src, i) => {
            const t = document.createElement('img');
            t.src = src;
            t.className = 'thumb' + (i === idx ? ' active' : '');
            t.addEventListener('click', () => { idx = i; update(); });
            thumbs.appendChild(t);
        });
    }

    function update() {
        main.src = images[idx];
        [...document.querySelectorAll('.thumb')].forEach((el, i) =>
            el.classList.toggle('active', i === idx)
        );
    }

    // 🟢 Свайп жесты
    let startX = 0;
    main.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; });
    main.addEventListener('touchend', (e) => {
        const endX = e.changedTouches[0].clientX;
        const diff = endX - startX;
        if (Math.abs(diff) > 50) { // свайп
            idx = (idx + (diff > 0 ? -1 : 1) + images.length) % images.length;
            update();
        }
    });

    renderThumbs();
    update();
}


// ========== КОРЗИНА ==========
function addToCartFromCard(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product) return;

    const availableSizes = product.sizes || [];
    if (availableSizes.length === 1) {
        const autoSize = availableSizes[0];
        const cartItem = {
            id: Date.now(),
            productId: product.id,
            name: product.name,
            price: product.price,
            size: autoSize,
            color: product.color,
            image: product.image,
            quantity: 1
        };
        cart.push(cartItem);
        saveCart();

        tg.showPopup({
            title: "Добавлено в корзину",
            message: `${product.name} (${autoSize}) добавлен в корзину!`,
            buttons: [{ type: "ok" }]
        });
    } else if (availableSizes.length > 1) {
        openProduct(productId);
        tg.showPopup({
            title: "Выберите размер",
            message: "Пожалуйста, выберите размер товара",
            buttons: [{ type: "ok" }]
        });
    } else {
        tg.showPopup({
            title: "Ошибка",
            message: "Нет доступных размеров для этого товара",
            buttons: [{ type: "ok" }]
        });
    }
}
function buyNow(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product) return;

    addToCartFromCard(productId);
    openCart();
}

function addToCartFromDetail() {
    if (!currentProduct) return;

    if (!selectedSize) {
        tg.showPopup({
            title: "Выберите размер",
            message: "Пожалуйста, выберите размер перед добавлением в корзину",
            buttons: [{ type: "ok" }]
        });
        
    }

    const cartItem = {
        id: Date.now(),
        productId: currentProduct.id,
        name: currentProduct.name,
        price: currentProduct.price,
        size: selectedSize,
        color: currentProduct.color,
        image: currentProduct.image,
        quantity: 1
    };

    cart.push(cartItem);
    saveCart();

    tg.showPopup({
        title: "Добавлено в корзину",
        message: `${currentProduct.name} (${selectedSize}) добавлен в корзину!`,
        buttons: [{ type: "ok" }]
    });
}

function openCart() {
    renderCart();
    showPage('cart');
}

function renderCart() {
    const cartContainer = document.getElementById('cart-items');
    const emptyCart = document.getElementById('empty-cart');
    const totalPriceElement = document.getElementById('total-price');

    if (!cartContainer || !emptyCart || !totalPriceElement) return;

    if (cart.length === 0) {
        cartContainer.innerHTML = '';
        emptyCart.style.display = 'block';
        totalPriceElement.textContent = '0';
        return;
    }

    emptyCart.style.display = 'none';
    const totalPrice = cart.reduce((total, item) => total + item.price * item.quantity, 0);
    totalPriceElement.textContent = totalPrice;

    cartContainer.innerHTML = cart.map(item => `
        <div class="cart-item">
            <img src="${item.image}" alt="${item.name}" class="cart-item-image" onerror="this.src='/static/images/placeholder.webp'">
            <div class="cart-item-info">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-details">Размер: ${item.size} | Цвет: ${item.color}</div>
                <div class="cart-item-price">${item.price}₽</div>
            </div>
            <button class="cart-item-remove" onclick="removeFromCart(${item.id})">🗑️</button>
        </div>
    `).join('');
}

function removeFromCart(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    saveCart();
    renderCart();
}

// ========== ОФОРМЛЕНИЕ ЗАКАЗА ==========
function checkout() {
    if (cart.length === 0) {
        tg.showAlert("Корзина пуста!");
        return;
    }

    const totalPrice = cart.reduce((t, i) => t + i.price * i.quantity, 0);
    const user = tg.initDataUnsafe.user || {};
    const orderData = {
        products: cart,
        total_price: totalPrice,
        user
    };

    tg.showConfirm("Отправить заказ менеджеру?", (confirmed) => {
        if (!confirmed) return;
        tg.MainButton.showProgress();

        fetch("/api/order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(orderData)
        })
            .then(res => res.json())
            .then(data => {
                tg.MainButton.hideProgress();
                if (data.status === "success") {
                    cart = [];
                    saveCart();
                    renderCart();
                    showPage('home');
                    tg.showAlert("✅ Заказ отправлен!");
                } else throw new Error(data.detail);
            })
            .catch(error => {
                tg.MainButton.hideProgress();
                tg.showAlert("❌ Ошибка: " + error.message);
            });
    });
}
function shareProduct() {
  if (!currentProduct) return;

  const botUsername = "botchickcalis_bot";
  const link = `https://t.me/${botUsername}?start=store_${currentProduct.id}`;
  const text = `👕 ${currentProduct.name} — ${currentProduct.price}₽\n${currentProduct.description}\n\n${link}`;

  tg.showPopup({
    title: "Поделиться товаром",
    message: "Скопируй ссылку и отправь другу в Telegram:",
    buttons: [
      { id: "copy", type: "ok", text: "📋 Скопировать ссылку" },
      { type: "cancel", text: "Закрыть" }
    ]
  });

  // Обработчик кнопок
  window.Telegram.WebApp.onEvent('popupClosed', function (event) {
    if (event.button_id === "copy") {
      navigator.clipboard.writeText(link);
      tg.showAlert("Ссылка скопирована!");
    }
  });
}

function sendToFriend() {
  if (!currentProduct) return;

  tg.showPopup({
    title: "Отправить другу",
    message: "Введи @username друга (например, @rustem)",
    buttons: [
      { id: "send", type: "ok", text: "Отправить" },
      { type: "cancel" },
    ]
  });

  // ⚠️ Примерно, если хочешь сделать ввод — можно позже заменить на форму Telegram WebAppInput
  // Для теста отправим прямо себе:
  const chatId = tg.initDataUnsafe?.user?.id; // пока отправляем самому себе

  fetch("/api/share", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      product_id: currentProduct.id
    })
  })
    .then(res => res.json())
    .then(data => {
      tg.showAlert("✅ Товар отправлен!");
    })
    .catch(err => {
      console.error(err);
      tg.showAlert("❌ Ошибка при отправке");
    });
}

