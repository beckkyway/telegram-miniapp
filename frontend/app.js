const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

let currentProduct = null;
let selectedSize = null;
let cart = [];
let allProducts = [];
let pageHistory = ['home'];

// ========== ЛОКАЛЬНОЕ ХРАНИЛИЩЕ ==========
function loadCart() {
    const savedCart = localStorage.getItem('calistor_cart');
    if (savedCart) {
        cart = JSON.parse(savedCart);
    }
    updateCartCount();
}

function saveCart() {
    localStorage.setItem('calistor_cart', JSON.stringify(cart));
    updateCartCount();
}

function updateCartCount() {
    const count = cart.reduce((total, item) => total + item.quantity, 0);
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = count;
    }
}

// ========== НАВИГАЦИЯ ==========
function showPage(pageName) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    const targetPage = document.getElementById(pageName + '-page');
    if (targetPage) {
        targetPage.classList.add('active');
        pageHistory.push(pageName);
    }
}

function goBack() {
    if (pageHistory.length > 1) {
        pageHistory.pop();
        const previousPage = pageHistory[pageHistory.length - 1];
        showPage(previousPage);
    } else {
        showPage('home');
    }
}

// ========== ЗАГРУЗКА ТОВАРОВ ==========
document.addEventListener('DOMContentLoaded', function () {
    // 1. Определение функции
    function loadMainBanner() {
        const bannerImg = document.getElementById('main-banner');

        if (bannerImg) {
            // 🟢 Логика обхода кэша
            const timestamp = new Date().getTime();
            bannerImg.src = `/static/images/banner.webp?t=${timestamp}`;
            console.log("Баннер загружен с обходом кэша.");
        }
    }
    
    // 2. Вызов функции
    loadCart();
    loadMainBanner(); // ✅ Вызываем функцию здесь, один раз при загрузке DOM

    // 3. Остальная логика (загрузка товаров)
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
}); // ✅ Здесь закрываем основной блок DOMContentLoaded

// ========== ОБРАБОТЧИК РАЗМЕРОВ ==========
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('size-btn')) {
        document.querySelectorAll('.size-btn').forEach(btn => {
            btn.classList.remove('selected');
        });
        e.target.classList.add('selected');
        selectedSize = e.target.dataset.size;
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
            <button class="add-to-cart-small" onclick="event.stopPropagation(); addToCartFromCard(${product.id})">
                В корзину
            </button>
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

    // Заполняем данные
    document.getElementById('product-title').textContent = product.name;
    document.getElementById('product-price').textContent = `${product.price}₽`;
    document.getElementById('product-color').textContent = product.color;
    document.getElementById('product-composition').textContent = product.composition;

    // Устанавливаем главное изображение
    const mainImages = product.images_large || [product.image_large];
    document.getElementById('product-main-image').src = mainImages[0] || product.image;

    // Создаем галерею миниатюр если есть несколько изображений
    const thumbnailsContainer = document.getElementById('product-thumbnails');
    if (mainImages.length > 1) {
        thumbnailsContainer.innerHTML = mainImages.map((img, index) => `
            <img src="${img}" class="thumbnail ${index === 0 ? 'active' : ''}" 
                 onclick="changeMainImage('${img}', this)">
        `).join('');
    } else {
        thumbnailsContainer.innerHTML = '';
    }

    document.getElementById('product-description-text').textContent = product.description;

    // Динамически создаем кнопки размеров
    const sizeButtonsContainer = document.getElementById('size-buttons');
    if (sizeButtonsContainer) {
        const availableSizes = product.sizes || [];

        if (availableSizes.length > 0) {
            sizeButtonsContainer.innerHTML = availableSizes.map(size => `
                <button class="size-btn" data-size="${size}">${size}</button>
            `).join('');
        } else {
            sizeButtonsContainer.innerHTML = '<p>Нет доступных размеров</p>';
        }
    }

    // Сбрасываем выбор размера
    document.querySelectorAll('.size-btn').forEach(btn => {
        btn.classList.remove('selected');
    });

    // Показываем страницу товара
    showPage('product');
}

// Функция для смены главного изображения
function changeMainImage(src, element) {
    document.getElementById('product-main-image').src = src;
    document.querySelectorAll('.thumbnail').forEach(thumb => {
        thumb.classList.remove('active');
    });
    element.classList.add('active');
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

function addToCartFromDetail() {
    if (!currentProduct) return;

    if (!selectedSize) {
        tg.showPopup({
            title: "Выберите размер",
            message: "Пожалуйста, выберите размер перед добавлением в корзину",
            buttons: [{ type: "ok" }]
        });
        return;
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

    const totalPrice = cart.reduce((total, item) => total + (item.price * item.quantity), 0);
    totalPriceElement.textContent = totalPrice;

    cartContainer.innerHTML = cart.map(item => `
        <div class="cart-item">
            <img src="${item.image}" alt="${item.name}" class="cart-item-image" onerror="this.src='/static/images/placeholder.webp'">
            <div class="cart-item-info">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-details">
                    Размер: ${item.size} | Цвет: ${item.color}
                </div>
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

    const totalPrice = cart.reduce((total, item) => total + (item.price * item.quantity), 0);
    const user = tg.initDataUnsafe.user || {};

    const orderData = {
        products: cart,
        total_price: totalPrice,
        user: {
            id: user.id,
            first_name: user.first_name,
            username: user.username,
            language_code: user.language_code
        }
    };

    tg.showConfirm("Отправить заказ менеджеру?", (confirmed) => {
        if (confirmed) {
            tg.MainButton.showProgress();

            fetch("/api/order", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(orderData)
            })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => { throw new Error(err.detail) });
                    }
                    return response.json();
                })
                .then(data => {
                    tg.MainButton.hideProgress();

                    if (data.status === "success") {
                        cart = [];
                        saveCart();
                        renderCart();
                        showPage('home');

                        tg.showAlert("✅ Заказ отправлен! Менеджер свяжется с вами в ближайшее время.");
                    } else {
                        throw new Error(data.detail);
                    }
                })
                .catch(error => {
                    tg.MainButton.hideProgress();
                    console.error("Order error:", error);
                    tg.showAlert("❌ Ошибка отправки заказа: " + error.message);
                });
        }
    });
}