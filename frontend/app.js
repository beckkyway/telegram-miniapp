const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

let currentProduct = null;
let selectedSize = null;
let cart = [];
let pageHistory = ['home']; // отслеживаем историю страниц

// Загружаем корзину из localStorage
function loadCart() {
    const savedCart = localStorage.getItem('calistor_cart');
    if (savedCart) {
        cart = JSON.parse(savedCart);
    }
    updateCartCount();
}

// Сохраняем корзину в localStorage
function saveCart() {
    localStorage.setItem('calistor_cart', JSON.stringify(cart));
    updateCartCount();
}

// Обновляем счетчик корзины
function updateCartCount() {
    const count = cart.reduce((total, item) => total + item.quantity, 0);
    document.getElementById('cart-count').textContent = count;
}

// Показать страницу
function showPage(pageName) {
    // Скрываем все страницы
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Показываем нужную страницу
    document.getElementById(pageName + '-page').classList.add('active');
    
    // Добавляем в историю
    pageHistory.push(pageName);
}

// Вернуться назад
function goBack() {
    if (pageHistory.length > 1) {
        // Удаляем текущую страницу из истории
        pageHistory.pop();
        
        // Получаем предыдущую страницу
        const previousPage = pageHistory[pageHistory.length - 1];
        
        // Показываем предыдущую страницу
        showPage(previousPage);
    } else {
        // Если история пуста, показываем главную
        showPage('home');
    }
}

// Загружаем товары при запуске
document.addEventListener('DOMContentLoaded', function() {
    loadCart();
    
    fetch("/api/products")
      .then(res => {
        if (!res.ok) throw new Error('Ошибка загрузки товаров');
        return res.json();
      })
      .then(products => {
        renderProducts(products);
      })
      .catch(error => {
        console.error('Error:', error);
        document.getElementById("product-list").innerHTML = '<p>Ошибка загрузки товаров</p>';
      });
});

// Рендер списка товаров
function renderProducts(products) {
  const container = document.getElementById("product-list");
  container.innerHTML = products.map(product => `
    <div class="product" onclick="openProduct(${product.id})">
      <img src="${product.image}" alt="${product.name}" />
      <h3>${product.name}</h3>
      <p>${product.price}₽</p>
    </div>
  `).join("");
}

// Открыть страницу товара
function openProduct(productId) {
  fetch("/api/products")
    .then(res => res.json())
    .then(products => {
      const product = products.find(p => p.id === productId);
      if (product) {
        showProductDetail(product);
      }
    });
}

// Показать детали товара
function showProductDetail(product) {
  currentProduct = product;
  selectedSize = null;
  
  // Заполняем данные
  document.getElementById('product-title').textContent = product.name;
  document.getElementById('product-price').textContent = `${product.price}₽`;
  document.getElementById('product-color').textContent = product.color;
  document.getElementById('product-composition').textContent = product.composition;
  document.getElementById('product-main-image').src = product.image;
  document.getElementById('product-description-text').textContent = product.description;
  
  // Сбрасываем выбор размера
  document.querySelectorAll('.size-btn').forEach(btn => {
    btn.classList.remove('selected');
  });
  
  // Показываем страницу товара
  showPage('product');
}

// Выбор размера
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('size-btn')) {
        // Снимаем выделение со всех кнопок
        document.querySelectorAll('.size-btn').forEach(btn => {
            btn.classList.remove('selected');
        });
        
        // Выделяем выбранную кнопку
        e.target.classList.add('selected');
        selectedSize = e.target.dataset.size;
    }
});

// Добавить в корзину со страницы товара
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

  // Добавляем товар в корзину
  const cartItem = {
    id: Date.now(), // уникальный ID для элемента корзины
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

// Открыть корзину
function openCart() {
    renderCart();
    showPage('cart');
}

// Рендер корзины
function renderCart() {
    const cartContainer = document.getElementById('cart-items');
    const emptyCart = document.getElementById('empty-cart');
    const totalPriceElement = document.getElementById('total-price');
    
    if (cart.length === 0) {
        cartContainer.innerHTML = '';
        emptyCart.style.display = 'block';
        totalPriceElement.textContent = '0';
        return;
    }
    
    emptyCart.style.display = 'none';
    
    // Считаем общую сумму
    const totalPrice = cart.reduce((total, item) => total + (item.price * item.quantity), 0);
    totalPriceElement.textContent = totalPrice;
    
    // Рендерим товары
    cartContainer.innerHTML = cart.map(item => `
        <div class="cart-item">
            <img src="${item.image}" alt="${item.name}" class="cart-item-image">
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

// Удалить из корзины
function removeFromCart(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    saveCart();
    renderCart();
}

// Оформить заказ
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
            // Показываем индикатор загрузки
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
                    // Очищаем корзину
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