// Конфигуратор ПК: динамическое добавление/удаление компонентов, обновление сборки

// --- SVG-иконки для sidebar ---
const CATEGORY_ICONS = {
  'Видеокарты': `<img src="/media/card.png" alt="Видеокарта" class="w-6 h-6 mr-2" style="object-fit:contain;">`,
  'Процессоры': `<img src="/media/cpu.png" alt="Видеокарта" class="w-6 h-6 mr-2" style="object-fit:contain;">`,
  'Материнские платы': `<img src="/media/mother.png" alt="Видеокарта" class="w-6 h-6 mr-2" style="object-fit:contain;">`,
  'Накопители': `<img src="/media/ssd.png" alt="Видеокарта" class="w-6 h-6 mr-2" style="object-fit:contain;">`,
  'Корпуса': `<img src="/media/body.png" alt="Видеокарта" class="w-6 h-6 mr-2" style="object-fit:contain;">`,
  'Оперативная память': `<img src="/media/ram.png" alt="Видеокарта" class="w-6 h-6 mr-2" style="object-fit:contain;">`,
  'Системы охлаждения': `<img src="/media/cool.png" alt="Видеокарта" class="w-6 h-6 mr-2" style="object-fit:contain;">`,
  'Блоки питания': `<img src="/media/psy.png" alt="Видеокарта" class="w-6 h-6 mr-2" style="object-fit:contain;">`,
};

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `mb-4 p-4 rounded-lg shadow-lg transition-all duration-300 ${type === 'success' ? 'bg-green-500' : 'bg-red-500'} text-white`;
  toast.textContent = message;
  const container = document.getElementById('toast-container');
  container.appendChild(toast);
  setTimeout(() => toast.classList.add('opacity-0'), 2500);
  setTimeout(() => toast.remove(), 3000);
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

let selectedCategoryId = null;
let lastSavedBuildId = null;
let allCategories = [];
let allProducts = [];
let currentFilters = [];
let currentCategoryId = null;

// Глобальная переменная для состояния чекбокса совместимости

// Загрузка категорий с иконками
async function loadCategories() {
  const res = await fetch('/pcbuilder/api/categories/');
  const data = await res.json();
  allCategories = data.categories;
  
  // Отладочная информация - посмотрите в консоли браузера
 
  
  const list = document.getElementById('category-list');
  list.innerHTML = '';
  data.categories.forEach(cat => {
   
    
    const li = document.createElement('li');
    li.innerHTML = `<button class="w-full flex items-center px-4 py-3 rounded-xl transition-colors font-medium text-lg ${selectedCategoryId === cat.id ? 'bg-gray-200 text-gray-900 dark:bg-gray-700 dark:text-white' : 'text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-[#23283a]'}" data-id="${cat.id}">
      ${(CATEGORY_ICONS[cat.name] || '<span class=\'w-6 h-6 mr-2\'>🖥️</span>')}
      <span class="whitespace-nowrap">${cat.name}</span>
    </button>`;
    li.querySelector('button').onclick = () => {
      selectedCategoryId = cat.id;
      loadCategories();
      loadCategoryFilters(cat.id);
    };
    list.appendChild(li);
  });
}

// Функция загрузки фильтров для категории
function loadCategoryFilters(categoryId) {
  currentCategoryId = categoryId;
  
  // Находим название выбранной категории
  const selectedCategory = allCategories.find(cat => cat.id === categoryId);
  
  fetch(`/pcbuilder/api/category-filters/?category=${categoryId}`)
    .then(response => response.json())
    .then(data => {
      currentFilters = data.filters || [];
      updateFilterSelects();
      loadProducts();
      
      // Показываем информацию о количестве доступных фильтров
      if (currentFilters.length > 0) {
        console.log(`Загружено ${currentFilters.length} фильтров для категории "${selectedCategory?.name}":`, 
                   currentFilters.map(f => f.name));
      } else {
        console.log(`Для категории "${selectedCategory?.name}" фильтры не найдены`);
      }
    })
    .catch(error => {
      console.error('Ошибка загрузки фильтров:', error);
      showToast('Ошибка загрузки фильтров', 'error');
    });
}

// Обновление селектов фильтров
function updateFilterSelects() {
  const filter1 = document.getElementById('filter-1');
  const filter2 = document.getElementById('filter-2');
  const filtersContainer = document.getElementById('filters-container');
  
  // Показываем контейнер фильтров только если есть фильтры
  if (currentFilters.length > 0) {
    filtersContainer.style.display = 'flex';
  } else {
    filtersContainer.style.display = 'none';
    return;
  }
  
  // Очищаем фильтры
  filter1.innerHTML = '<option value="">Выберите спецификацию</option>';
  filter2.innerHTML = '<option value="">Выберите спецификацию</option>';
  
  // Сбрасываем dataset
  delete filter1.dataset.spec;
  delete filter2.dataset.spec;
  
  // Сбрасываем подписи
  document.getElementById('filter-1-label').textContent = 'Фильтр 1';
  document.getElementById('filter-2-label').textContent = 'Фильтр 2';
  
  // Добавляем чекбокс совместимости, если ещё не добавлен
  // Заполняем оба фильтра доступными спецификациями
  currentFilters.forEach(filter => {
    const option1 = document.createElement('option');
    option1.value = filter.id;
    option1.textContent = filter.name + (filter.unit ? ` (${filter.unit})` : '');
    filter1.appendChild(option1);
    
    const option2 = document.createElement('option');
    option2.value = filter.id;
    option2.textContent = filter.name + (filter.unit ? ` (${filter.unit})` : '');
    filter2.appendChild(option2);
  });
}

// Функция сброса конкретного фильтра
function resetFilter(filterId) {
  const filter = document.getElementById(filterId);
  const labelId = filterId + '-label';
  const labelText = filterId === 'filter-1' ? 'Фильтр 1' : 'Фильтр 2';
  
  // Создаем новый селект
  const newSelect = document.createElement('select');
  newSelect.id = filterId;
  newSelect.className = filter.className;
  
  // Заполняем спецификациями
  newSelect.innerHTML = '<option value="">Выберите спецификацию</option>';
  currentFilters.forEach(filterItem => {
    const option = document.createElement('option');
    option.value = filterItem.id;
    option.textContent = filterItem.name + (filterItem.unit ? ` (${filterItem.unit})` : '');
    newSelect.appendChild(option);
  });
  
  // Сбрасываем подпись
  document.getElementById(labelId).textContent = labelText;
  
  // Заменяем элемент
  filter.parentNode.replaceChild(newSelect, filter);
}

// Обновление значений для выбранной спецификации
function updateFilterValues(filterElement, specId, labelElement) {
  const selectedFilter = currentFilters.find(f => f.id == specId);
  if (!selectedFilter) return;
  
  // Обновляем подпись фильтра
  labelElement.textContent = selectedFilter.name + (selectedFilter.unit ? ` (${selectedFilter.unit})` : '');
  
  // Очищаем и добавляем пустой вариант
  filterElement.innerHTML = '<option value="">Все значения</option>';
  
  // Добавляем значения
  selectedFilter.values.forEach(value => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    filterElement.appendChild(option);
  });
}

// Более простой подход с делегированием событий
function setupFilterHandlers() {
  const filtersContainer = document.getElementById('filters-container');
  
  // Удаляем старые обработчики
  filtersContainer.removeEventListener('change', handleFilterChange);
  filtersContainer.removeEventListener('click', handleClearFilters);
  
  // Добавляем новые обработчики с делегированием
  filtersContainer.addEventListener('change', handleFilterChange);
  filtersContainer.addEventListener('click', handleClearFilters);
}

function handleFilterChange(event) {
  const target = event.target;
  
  if (target.id === 'filter-1' || target.id === 'filter-2') {
    const filterId = target.id;
    const labelId = filterId + '-label';
    
    if (target.value && !target.dataset.spec) {
      // Выбрана спецификация - превращаем в селект значений
      const newSelect = document.createElement('select');
      newSelect.id = filterId;
      newSelect.className = target.className;
      newSelect.dataset.spec = target.value;
      
      const label = document.getElementById(labelId);
      updateFilterValues(newSelect, target.value, label);
      
      target.parentNode.replaceChild(newSelect, target);
    } else if (target.dataset.spec && target.value) {
      // Выбрано значение - фильтруем товары
      loadProducts();
    } else if (target.dataset.spec && !target.value) {
      // Выбрано "Все значения" - сбрасываем этот фильтр
      resetFilter(filterId);
      loadProducts();
    } else if (!target.value && !target.dataset.spec) {
      // Сброс фильтра на уровне выбора спецификации
      loadProducts();
    }
  }
}

function handleClearFilters(event) {
  if (event.target.id === 'clear-filters') {
    clearFilters();
  }
}

// Упрощенная функция очистки всех фильтров
function clearFilters() {
  resetFilter('filter-1');
  resetFilter('filter-2');
  loadProducts();
}

// Обновленная функция загрузки товаров с фильтрами
function loadProducts() {
  if (!currentCategoryId) return;
  
  const filter1Select = document.getElementById('filter-1');
  const filter2Select = document.getElementById('filter-2');
  
  let url = `/pcbuilder/api/products/?category=${currentCategoryId}`;
  
  // Добавляем фильтры если они выбраны
  if (filter1Select.dataset.spec && filter1Select.value) {
    url += `&filter1_spec=${filter1Select.dataset.spec}&filter1_value=${filter1Select.value}`;
  }
  
  if (filter2Select.dataset.spec && filter2Select.value) {
    url += `&filter2_spec=${filter2Select.dataset.spec}&filter2_value=${filter2Select.value}`;
  }
  
  // Если включён фильтр совместимости (чекбокс) для этой категории
  url += `&compatible_only=1`;
  
  fetch(url)
    .then(response => response.json())
    .then(data => {
      renderProducts(data.products || []);
    })
    .catch(error => {
      console.error('Ошибка загрузки товаров:', error);
    });
}

// Рендер карточек товаров
function renderProducts(products) {
  const list = document.getElementById('products-list');
  list.innerHTML = '';
  if (!products || products.length === 0) {
    list.innerHTML = '<p class="text-gray-500 dark:text-gray-400">Товары не найдены.</p>';
    return;
  }
  products.forEach(prod => {
    const finalPrice = prod.discount ?   (prod.price * (1 - prod.discount / 100)) : prod.price;
    const card = document.createElement('div');
    card.className = 'flex flex-col bg-gray-100 dark:bg-[#181C27] rounded-2xl p-6 shadow relative';
    card.innerHTML = `
      <div class="w-full h-[160px] bg-gray-200 dark:bg-[#23283a] flex items-center justify-center rounded-xl text-3xl text-[#b0b0b0] dark:text-[#7a8599] font-bold mb-4">
      <img src="${prod.image}" alt="${prod.name}" class="w-full h-full object-cover rounded-xl">
      </div>
      <div class="flex-1 flex flex-col gap-1">
        <a href="/catalog/${prod.product_line_slug}/${prod.category_slug}/${prod.product_slug}/" class="text-lg font-bold text-gray-900 dark:text-white hover:underline" title="${prod.name}" target="_blank">${prod.name}</a>
        <div class="text-[#7a85ff] text-base font-semibold mb-1"> ${finalPrice} ₽</div>
        <div class="flex flex-col gap-1 text-xs text-gray-600 dark:text-gray-300 mb-1 characteristics-container">
          ${(prod.specs || []).slice(0, 4).map(s => `<span><span class="font-medium">${s.specification__name}:</span> ${s.value}${s.specification__unit ? ' ' + s.specification__unit : ''}</span>`).join('')}
        </div>
      </div>
      ${(prod.specs && prod.specs.length > 0) ? `<button class="toggle-characteristics-btn rounded-xl px-4 py-2 text-sm font-semibold transition-colors duration-300 mt-2 
        border border-[#222222] hover:bg-[#e5e7fa] hover:border-gray-500 hover:text-[#7a85ff] text-[#222222] 
        dark:bg-transparent dark:text-[#FFFFFF] dark:border-[#FFFFFF] dark:hover:border-gray-300 dark:hover:text-[#7a85ff] dark:hover:bg-[#23283a]
        cursor-pointer focus:outline-none">Характеристики</button>` : ''}
      <button 
        class="w-full px-6 py-2 rounded-xl text-base font-bold transition-colors select-product-btn mt-4
          ${prod.stock === 0 ? 'bg-gray-400 text-white cursor-not-allowed opacity-60' : (prod.is_selected ? 'bg-red-500 hover:bg-red-700 text-white' : 'bg-[#7a85ff] hover:bg-[#4b1bb3] text-white')}"
        data-id="${prod.id}"
        ${prod.stock === 0 ? 'disabled' : ''}
      >
        ${prod.stock === 0 ? 'Нет в наличии' : (prod.is_selected ? 'Убрать' : 'Выбрать')}
      </button>
    `;
    const selectBtn = card.querySelector('.select-product-btn');
    if (prod.stock === 0) {
      selectBtn.disabled = true;
      selectBtn.onclick = null;
    } else if (prod.is_selected) {
      selectBtn.onclick = () => removeFromBuild(prod.id);
    } else {
      selectBtn.onclick = () => addToBuild(prod.id);
    }
    const toggleBtn = card.querySelector('.toggle-characteristics-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            showCharacteristicsModal(prod.name, prod.specs);
        });
    }
    list.appendChild(card);
  });
}

// Функция для отображения характеристик в модальном окне
function showCharacteristicsModal(productName, specs) {
  const modal = document.getElementById('characteristics-modal');
  const modalProductName = document.getElementById('modal-product-name');
  const modalCharacteristicsList = document.getElementById('modal-characteristics-list');

  modalProductName.textContent = `Характеристики: ${productName}`;
  modalCharacteristicsList.innerHTML = '';

  if (specs && specs.length > 0) {
    specs.forEach(s => {
      const p = document.createElement('p');
      p.className = 'text-gray-700 dark:text-gray-200 mb-2';
      p.innerHTML = `<span class="font-medium">${s.specification__name}:</span> ${s.value}${s.specification__unit ? ' ' + s.specification__unit : ''}`;
      modalCharacteristicsList.appendChild(p);
    });
  } else {
    modalCharacteristicsList.innerHTML = '<p class="text-gray-500 dark:text-gray-400">Характеристики не найдены.</p>';
  }

  modal.classList.remove('hidden');
}

// Закрытие модального окна
document.addEventListener('DOMContentLoaded', () => {
  const closeModalBtn = document.getElementById('close-modal-btn');
  const modal = document.getElementById('characteristics-modal');

  if (closeModalBtn && modal) {
    closeModalBtn.addEventListener('click', () => {
      modal.classList.add('hidden');
    });
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.add('hidden');
      }
    });
  }
});

// Загрузка сборки
async function loadBuild() {
  const res = await fetch('/pcbuilder/api/build/');
  const data = await res.json();
  const list = document.getElementById('build-list');
  const total = document.getElementById('build-total');
  list.innerHTML = '';
  if (!data.components.length) {
    list.innerHTML = '<div class="text-gray-500 dark:text-gray-400 text-center">Добавьте компоненты</div>';
    total.textContent = '0 ₽';
    return;
  }
  data.components.forEach(comp => {
    const finalPrice = comp.discount ? comp.price * (1 - comp.discount / 100) : comp.price;
    const div = document.createElement('div');
    div.className = 'flex justify-between items-center border border-[#7a85ff] rounded-xl px-4 py-3';
    div.innerHTML = `
      <div>
        <div class="text-gray-400 text-sm font-semibold mb-1">${comp.category_name}</div>
        <div class="text-base font-bold text-black dark:text-white ">${comp.product_name}</div>
      </div>
      <div class="flex flex-col items-end">
        <span class="font-bold text-[#7a85ff] text-lg">${finalPrice} ₽</span>
        <button class="remove-btn text-red-500 hover:text-red-700 text-xl" title="Удалить" data-id="${comp.product_id}">&times;</button>
      </div>
    `;
    div.querySelector('.remove-btn').onclick = () => removeFromBuild(comp.product_id);
    list.appendChild(div);
  });
  total.textContent = data.total + ' ₽';
}

// Добавить компонент в сборку
async function addToBuild(productId) {
  const res = await fetch('/pcbuilder/api/build/add/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ product_id: productId })
  });
  const data = await res.json();
  if (data.success) {
    showToast('Компонент добавлен');
    lastSavedBuildId = null;
    loadBuild();
    loadProducts();
  } else {
    showToast(data.error || 'Ошибка', 'error');
  }
}

// Удалить компонент из сборки
async function removeFromBuild(productId) {
  const res = await fetch('/pcbuilder/api/build/remove/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ product_id: productId })
  });
  const data = await res.json();
  if (data.success) {
    showToast('Компонент удалён', 'error');
    lastSavedBuildId = null;
    loadBuild();
    loadProducts();
  } else {
    showToast(data.error || 'Ошибка', 'error');
  }
}

// Модальное окно для ввода имени сборки
function showSaveBuildModal() {
  let modal = document.getElementById('save-build-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'save-build-modal';
    modal.className = 'fixed inset-0 bg-black/30 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-white dark:bg-[#28303F] rounded-lg shadow-xl max-w-md w-full p-6 relative">
        <button class="absolute top-3 right-3 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-3xl font-bold" id="close-save-build-modal">&times;</button>
        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-4">Сохранить сборку</h3>
        <form id="save-build-form" class="flex flex-col gap-4">
          <input type="text" name="build_name" class="px-4 py-2 border rounded" placeholder="Название сборки" required maxlength="255">
          <div class="flex gap-2 justify-end">
            <button type="submit" class="bg-[#7a85ff] hover:bg-[#4b1bb3] text-white px-6 py-2 rounded-lg font-semibold">Сохранить</button>
            <button type="button" id="cancel-save-build" class="bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-lg font-semibold">Отмена</button>
          </div>
        </form>
      </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('close-save-build-modal').onclick = hideSaveBuildModal;
    document.getElementById('cancel-save-build').onclick = hideSaveBuildModal;
    document.getElementById('save-build-form').onsubmit = saveBuildWithName;
  }
  modal.classList.remove('hidden');
}

function hideSaveBuildModal() {
  const modal = document.getElementById('save-build-modal');
  if (modal) modal.classList.add('hidden');
}

async function saveBuildWithName(e) {
  e.preventDefault();
  const name = e.target.build_name.value.trim();
  if (!name) return;
  const res = await fetch('/pcbuilder/api/build/save/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ name })
  });
  const data = await res.json();
  if (data.success) {
    showToast('Сборка сохранена!');
    lastSavedBuildId = data.build_id;
    hideSaveBuildModal();
  } else {
    showToast(data.error || 'Ошибка', 'error');
  }
}

// Добавить сборку в корзину
async function addBuildToCart() {
  if (!lastSavedBuildId) {
    showToast('Сначала сохраните сборку', 'error');
    return;
  }
  // Сохранённая сборка — добавляем по id
  const res = await fetch('/pcbuilder/api/build/add_to_cart/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ build_id: lastSavedBuildId })
  });
  const data = await res.json();
  if (data.success) {
    showToast('Сборка добавлена в корзину!');
  } else {
    showToast(data.error || 'Ошибка', 'error');
  }
}

// Получить параметр из URL
function getUrlParam(name) {
  const url = new URL(window.location.href);
  return url.searchParams.get(name);
}

// Загрузить сохранённую конфигурацию и подставить в сборку
async function loadSavedConfigAndApply(configId) {
  console.log('Попытка автозагрузки конфигурации:', configId);
  // Получаем все сохранённые сборки пользователя
  const res = await fetch('/pcbuilder/api/builds/');
  const data = await res.json();
  console.log('Ответ /pcbuilder/api/builds/:', data);
  if (!data.success) return;

  const config = (data.configurations || []).find(c => c.id == configId || c.id == +configId);
  console.log('Найдена конфигурация:', config);
  if (!config) {
    showToast('Конфигурация не найдена', 'error');
    return;
  }

  // Очищаем текущую сборку
  const buildRes = await fetch('/pcbuilder/api/build/');
  const buildData = await buildRes.json();
  for (const comp of buildData.components) {
    console.log('Удаляем компонент:', comp.product_id);
    await fetch('/pcbuilder/api/build/remove/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ product_id: comp.product_id })
    });
  }

  // Добавляем компоненты из сохранённой конфигурации
  for (const comp of config.components) {
    console.log('Добавляем компонент:', comp.product_id);
    await fetch('/pcbuilder/api/build/add/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ product_id: comp.product_id })
    });
  }

  lastSavedBuildId = config.id;

  showToast('Конфигурация загружена!');
  loadBuild();

  // Сбросить параметр load_config из URL
  const url = new URL(window.location.href);
  url.searchParams.delete('load_config');
  window.history.replaceState({}, document.title, url.pathname + url.search);
  console.log('Параметр load_config удалён из URL');
}

// При загрузке страницы — если есть load_config, подгружаем конфиг
window.addEventListener('DOMContentLoaded', async () => {
  loadCategories();
  loadBuild();
  setupFilterHandlers();
  
  document.getElementById('save-build-btn').onclick = showSaveBuildModal;
  document.getElementById('add-to-cart-btn').onclick = addBuildToCart;

  const configId = getUrlParam('load_config');
  if (configId) {
    await loadSavedConfigAndApply(configId);
  }
});
