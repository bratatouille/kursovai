(function() {
    'use strict';
    
    // Ждем загрузки DOM и jQuery
    function waitForjQuery(callback) {
        if (typeof django !== 'undefined' && django.jQuery) {
            callback(django.jQuery);
        } else if (typeof $ !== 'undefined') {
            callback($);
        } else {
            setTimeout(function() {
                waitForjQuery(callback);
            }, 100);
        }
    }
    
    function updateProductOptions(categorySelect, productSelect, $) {
        const categoryId = categorySelect.val();
        
        if (!categoryId) {
            productSelect.empty().append('<option value="">---------</option>');
            return;
        }
        
        // Показываем индикатор загрузки
        productSelect.empty().append('<option value="">Загрузка...</option>');
        
        // AJAX запрос для получения товаров категории
        $.ajax({
            url: '/pcbuilder/get-products-by-category/',
            data: {
                'category_id': categoryId
            },
            success: function(data) {
                const selectedOption = productSelect.find('option:selected');
                const selectedValue = selectedOption.val();
                const selectedText = selectedOption.text();

                productSelect.empty();
                productSelect.append('<option value="">---------</option>');

                let selectedValueInNewList = false;
                if (data.products) {
                    $.each(data.products, function(index, product) {
                        if (product.id == selectedValue) {
                            selectedValueInNewList = true;
                        }
                        productSelect.append(
                            '<option value="' + product.id + '">' + product.name + '</option>'
                        );
                    });
                }

                // Если исходно выбранный элемент не пришел в новом списке
                // (из-за несоответствия категорий), добавляем его обратно.
                if (selectedValue && selectedText && selectedText !== '---------' && !selectedValueInNewList) {
                    productSelect.append(
                        '<option value="' + selectedValue + '">' + selectedText + '</option>'
                    );
                }

                // Восстанавливаем выбор
                productSelect.val(selectedValue);
            },
            error: function(xhr, status, error) {
                console.error('AJAX Error:', error);
                productSelect.empty().append('<option value="">Ошибка загрузки</option>');
            }
        });
    }
    
    function initializeCategoryProductFilter($) {
        // Функция для привязки событий к элементам
        function bindEvents() {
            // Удаляем старые обработчики чтобы избежать дублирования
            $(document).off('change.categoryFilter', '.category-select');
            
            // Привязываем новый обработчик
            $(document).on('change.categoryFilter', '.category-select', function() {
                const $categorySelect = $(this);
                const $row = $categorySelect.closest('.form-row, tr, .field-category').parent();
                const $productSelect = $row.find('.product-select');
                
                if ($productSelect.length > 0) {
                    updateProductOptions($categorySelect, $productSelect, $);
                }
            });
        }
        
        // Инициализируем события
        bindEvents();
        
        // Обработка добавления новых инлайн форм
        $(document).on('click', '.add-row a, .grp-add-handler', function() {
            setTimeout(function() {
                bindEvents();
            }, 500);
        });
        
        // Для Django Grappelli (если используется)
        $(document).on('formset:added', function() {
            setTimeout(function() {
                bindEvents();
            }, 500);
        });
    }
    
    // Инициализация после загрузки DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            waitForjQuery(initializeCategoryProductFilter);
        });
    } else {
        waitForjQuery(initializeCategoryProductFilter);
    }
    
})();
