        /* ==========================================================================
           КОНФИГУРАЦИЯ ПОДКЛЮЧЕНИЯ К НАШЕЙ СЕРВЕРНОЙ БД (BACKEND API)
           Пользователю это не видно. Все действия отправляются сюда через fetch().
           ========================================================================== */
        const API_CONFIG = {
            BASE_URL: window.location.origin.startsWith('http') ? '/api' : 'http://127.0.0.1:5001/api',
            ENDPOINTS: {
                REGISTER: '/auth/register',
                LOGIN: '/auth/login',
                BOOKINGS: '/bookings',
                SERVICES: '/services',
                RECALCULATE: '/services/recalculate'
            }
        };

        // Запрос к серверу. Автоматически пробует текущий адрес и 127.0.0.1 (для обхода VPN/прокси)
        async function apiRequest(method, endpoint, payload) {
            const headers = { 'Content-Type': 'application/json' };
            if (activeUser && activeUser.login) {
                headers['X-User-Login'] = activeUser.login;
                headers['X-User-Id'] = String(activeUser.id || '');
            }
            const options = {
                method,
                headers
            };
            if (payload !== undefined) options.body = JSON.stringify(payload);

            const candidates = [];
            if (endpoint.startsWith('http')) {
                candidates.push(endpoint);
            } else {
                candidates.push(API_CONFIG.BASE_URL + endpoint);
                const loopback1 = 'http://127.0.0.1:5001/api' + endpoint;
                const loopback2 = 'http://localhost:5001/api' + endpoint;
                if (!candidates.includes(loopback1)) candidates.push(loopback1);
                if (!candidates.includes(loopback2)) candidates.push(loopback2);
            }

            let lastErr = null;
            for (const url of candidates) {
                try {
                    const response = await fetch(url, options);
                    const contentType = response.headers.get('content-type') || '';
                    if (contentType.includes('application/json')) {
                        return await response.json();
                    }
                    const text = await response.text();
                    return { ok: response.ok, error: text || `Ошибка сервера (${response.status})` };
                } catch (err) {
                    lastErr = err;
                }
            }

            console.error('[API] Ошибка соединения:', endpoint, lastErr);
            return {
                ok: false,
                offline: true,
                error: 'Сервер недоступен. Откройте страницу http://localhost:5001 (и отключите VPN в браузере, если он включён).'
            };
        }

        /* ==========================================================================
           КАТАЛОГ УСЛУГ ПАРИКМАХЕРСКОЙ (Стрижки, окрашивание, доп. услуги, товары)
           ========================================================================== */
        const DEFAULT_SERVICES = [
            {
                id: 1,
                title: "Женская модельная стрижка + укладка",
                category: "Стрижки",
                price: 2800,
                duration: "60 мин",
                emoji: "✂️",
                image: "",
                desc: "Мытьё головы с расслабляющим массажем, подбор формы стрижки и лёгкая укладка феном."
            },
            {
                id: 2,
                title: "Мужская стрижка (Классика / Fade)",
                category: "Стрижки",
                price: 1900,
                duration: "45 мин",
                emoji: "💈",
                image: "",
                desc: "Точная работа ножницами и машинкой, окантовка, мытьё головы и укладка матовой пастой."
            },
            {
                id: 3,
                title: "Стрижка чёлки и коррекция кончиков",
                category: "Доп. услуги",
                price: 900,
                duration: "25 мин",
                emoji: "🌸",
                image: "",
                desc: "Быстрое обновление формы чёлки (шторка, прямая, рваная) и ровный срез секущихся кончиков."
            },
            {
                id: 4,
                title: "Окрашивание в один тон (Корни + длина)",
                category: "Окрашивание",
                price: 4800,
                duration: "120 мин",
                emoji: "🎨",
                image: "",
                desc: "Бережное безаммиачное окрашивание с глубоким блеском и защитой структуры волос."
            },
            {
                id: 5,
                title: "Сложное окрашивание AirTouch / Шатуш / Балаяж",
                category: "Окрашивание",
                price: 8900,
                duration: "180 мин",
                emoji: "✨",
                image: "",
                desc: "Создание плавного рельефного блонда или мягких бликов с тонированием и уходом."
            },
            {
                id: 6,
                title: "Кератиновое восстановление и ботокс волос",
                category: "Укладки и уход",
                price: 5200,
                duration: "110 мин",
                emoji: "🌿",
                image: "",
                desc: "Глубокое питание, разглаживание пушистости и зеркальный глянец на срок до 3 месяцев."
            },
            {
                id: 7,
                title: "Вечерняя укладка / Голливудские локоны",
                category: "Укладки и уход",
                price: 2600,
                duration: "60 мин",
                emoji: "💫",
                image: "",
                desc: "Стойкие воздушные локоны или элегантный низкий пучок для особого случая."
            },
            {
                id: 8,
                title: "Пилинг кожи головы + ампульный SPA-массаж",
                category: "Доп. услуги",
                price: 2100,
                duration: "40 мин",
                emoji: "🧖‍♀️",
                image: "",
                desc: "Детокс-очищение кожи головы, стимуляция роста волос и нанесение витаминной сыворотки."
            },
            {
                id: 9,
                title: "Оформление и окрашивание бровей",
                category: "Доп. услуги",
                price: 1400,
                duration: "35 мин",
                emoji: "👁️",
                image: "",
                desc: "Подбор архитектуры бровей, деликатная коррекция и стойкое окрашивание краской или хной."
            },
            {
                id: 10,
                title: "Увлажняющая маска с маслом арганы и шёлком",
                category: "Товары для дома",
                price: 2300,
                duration: "250 мл",
                emoji: "🧴",
                image: "",
                desc: "Профессиональная салонная маска для домашнего ухода за сухими и окрашенными волосами."
            }
        ];

        let servicesList = JSON.parse(localStorage.getItem('lumiere_client_services')) || DEFAULT_SERVICES;
        let clientBookings = JSON.parse(localStorage.getItem('lumiere_client_bookings')) || [];
        let activeUser = JSON.parse(localStorage.getItem('lumiere_active_user')) || null;
        let activeCategory = 'all';

        // Загрузка каталога из БД (если сервер недоступен — остаётся локальная копия)
        async function loadServicesFromDB() {
            const res = await apiRequest('GET', API_CONFIG.ENDPOINTS.SERVICES);
            if (res.ok) {
                servicesList = res.services.map(s => ({ ...s, desc: s.desc || '', duration: s.duration || '' }));
                saveState();
                renderCatalog();
            } else {
                showToast('⚠️ ' + res.error);
            }
        }

        // Загрузка записей вошедшего клиента из БД
        async function loadBookingsFromDB() {
            if (!activeUser || !activeUser.id) return;
            const res = await apiRequest('GET', API_CONFIG.ENDPOINTS.BOOKINGS + '?userId=' + activeUser.id);
            if (res.ok) { clientBookings = res.bookings; saveState(); }
        }

        function saveState() {
            localStorage.setItem('lumiere_client_services', JSON.stringify(servicesList));
            localStorage.setItem('lumiere_client_bookings', JSON.stringify(clientBookings));
            localStorage.setItem('lumiere_active_user', JSON.stringify(activeUser));
            document.getElementById('myBookingsCount').textContent = clientBookings.length;
        }

        // Проверка прав администратора
        function isAdmin() {
            return !!(activeUser && (activeUser.login === 'admin' || activeUser.isAdmin));
        }

        // Отображение кнопок управления только для администратора
        function updateAdminUI() {
            const admin = isAdmin();
            const heroBtn = document.getElementById('heroAddServiceBtn');
            const openBtn = document.getElementById('openAddModalBtn');
            const heroRecalc = document.getElementById('heroRecalcBtn');
            const openRecalc = document.getElementById('openRecalcModalBtn');
            if (heroBtn) heroBtn.style.display = admin ? 'inline-flex' : 'none';
            if (openBtn) openBtn.style.display = admin ? 'inline-flex' : 'none';
            if (heroRecalc) heroRecalc.style.display = admin ? 'inline-flex' : 'none';
            if (openRecalc) openRecalc.style.display = admin ? 'inline-flex' : 'none';
        }

        /* ==========================================================================
           ОТРИСОВКА КАТАЛОГА, ПОИСК И ФИЛЬТРАЦИЯ
           ========================================================================== */
        function renderCatalog() {
            const grid = document.getElementById('servicesGrid');
            const query = document.getElementById('searchField').value.trim().toLowerCase();
            const maxPrice = Number(document.getElementById('priceRange').value);
            const sortVal = document.getElementById('sortOrder').value;

            let filtered = servicesList.filter(item => {
                const matchText = item.title.toLowerCase().includes(query) ||
                                  item.desc.toLowerCase().includes(query) ||
                                  item.category.toLowerCase().includes(query);
                const matchCat = activeCategory === 'all' || item.category === activeCategory;
                const matchPrice = item.price <= maxPrice;
                return matchText && matchCat && matchPrice;
            });

            if (sortVal === 'asc') filtered.sort((a, b) => a.price - b.price);
            if (sortVal === 'desc') filtered.sort((a, b) => b.price - a.price);
            if (sortVal === 'name') filtered.sort((a, b) => a.title.localeCompare(b.title, 'ru'));

            if (filtered.length === 0) {
                grid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 50px; background: var(--bg-card); border-radius: var(--radius-xl); border: 1.5px dashed var(--border-color);">
                        <div style="font-size: 2.5rem; margin-bottom: 8px;">🍃</div>
                        <h3>Ничего не найдено</h3>
                        <p style="color: var(--text-muted);">Попробуйте увеличить максимальную цену или выбрать другую категорию.</p>
                    </div>
                `;
                return;
            }

            grid.innerHTML = filtered.map(item => `
                <article class="service-card">
                    <div class="card-photo">
                        ${item.image ? `<img src="${item.image}" alt="${item.title}">` : `
                            <div class="photo-emoji">${item.emoji || '✨'}</div>
                            <span class="photo-caption">Место для фото</span>
                        `}
                        <div class="card-top-badges">
                            <span class="pill-badge">${item.category}</span>
                            <span class="pill-badge pill-time">${item.duration}</span>
                        </div>
                    </div>
                    <div class="card-content">
                        <div class="card-cat-label">${item.category}</div>
                        <h3 class="card-title">${item.title}</h3>
                        <p class="card-desc">${item.desc}</p>
                        <div class="card-bottom">
                            <div class="card-price">${item.price.toLocaleString('ru-RU')} ₽</div>
                            <div class="card-btns">
                                <button type="button" class="btn btn-primary" data-book-id="${item.id}" style="padding: 9px 18px; font-size: 0.85rem;">
                                    Записаться
                                </button>
                                ${isAdmin() ? `
                                    <button type="button" class="btn btn-delete" data-del-id="${item.id}" title="Удалить карточку">
                                        🗑
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </article>
            `).join('');
        }

        /* ==========================================================================
           УПРАВЛЕНИЕ МОДАЛЬНЫМИ ОКНАМИ
           ========================================================================== */
        function openModal(id) {
            document.getElementById(id).classList.add('open');
        }

        function closeModal(id) {
            document.getElementById(id).classList.remove('open');
        }

        function showToast(text) {
            const holder = document.getElementById('toastHolder');
            const el = document.createElement('div');
            el.className = 'toast-msg';
            el.textContent = text;
            holder.appendChild(el);
            setTimeout(() => el.remove(), 3200);
        }

        function renderHeaderUser() {
            const box = document.getElementById('userHeaderBox');
            if (activeUser) {
                const adminBadge = isAdmin() 
                    ? `<span style="font-size: 0.72rem; font-weight: 700; background: var(--accent); color: white; padding: 2px 8px; border-radius: var(--radius-pill); margin-left: 6px;">Администратор</span>` 
                    : '';
                const pointsBadge = `<span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(217, 138, 108, 0.15); color: var(--accent); padding: 3px 10px; border-radius: var(--radius-pill); font-weight: 700; font-size: 0.82rem; border: 1px solid var(--border-color); margin-left: 4px;" title="Ваш бонусный счёт (кешбэк 5%)">💎 ${activeUser.points || 0} б.</span>`;
                box.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 8px; background: var(--accent-soft); padding: 6px 14px; border-radius: var(--radius-pill); border: 1px solid var(--border-color);">
                        <span style="font-weight: 700; font-size: 0.88rem;">👤 ${activeUser.name}${adminBadge}</span>
                        ${pointsBadge}
                        <button type="button" class="btn btn-soft" id="logoutBtn" style="padding: 5px 12px; font-size: 0.78rem;">Выйти</button>
                    </div>
                `;
                document.getElementById('logoutBtn').addEventListener('click', async () => {
                    await apiRequest('POST', '/auth/logout');
                    activeUser = null;
                    clientBookings = [];
                    saveState();
                    updateAdminUI();
                    renderHeaderUser();
                    renderCatalog();
                    showToast('Вы вышли из личного кабинета');
                });
            } else {
                box.innerHTML = `
                    <button type="button" class="btn btn-primary" id="openAuthBtn">
                        ✨ Войти в кабинет
                    </button>
                `;
                document.getElementById('openAuthBtn').addEventListener('click', () => openModal('authModal'));
            }
        }

        function renderMyBookingsModal() {
            const container = document.getElementById('myBookingsList');
            if (clientBookings.length === 0) {
                container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 24px 0;">У вас пока нет активных записей. Выберите любую услугу в каталоге!</p>`;
                return;
            }
            container.innerHTML = clientBookings.map(b => `
                <div class="booking-item">
                    <div>
                        <div style="font-weight: 700; font-size: 0.95rem;">${b.serviceTitle}</div>
                        <div style="font-size: 0.82rem; color: var(--text-muted);">Мастер: ${b.master} • ${b.date} в ${b.time}</div>
                        <div style="font-size: 0.85rem; font-weight: 700; color: var(--accent); margin-top: 2px;">
                            ${b.price.toLocaleString('ru-RU')} ₽
                            ${b.pointsEarned ? `<span style="color: #527D6C; font-size: 0.78rem; font-weight: 600; margin-left: 8px;">(+${b.pointsEarned} б. кешбэк)</span>` : ''}
                            ${b.pointsUsed ? `<span style="color: var(--accent); font-size: 0.78rem; font-weight: 600; margin-left: 4px;">(-${b.pointsUsed} б. списано)</span>` : ''}
                        </div>
                    </div>
                    <button type="button" class="btn btn-delete" data-cancel-booking="${b.id}">Отменить</button>
                </div>
            `).join('');
        }

        /* ==========================================================================
           ПРИВЯЗКА ВСЕХ КНОПОК И ИНТЕРАКТИВНЫХ ЭЛЕМЕНТОВ
           ========================================================================== */
        document.addEventListener('DOMContentLoaded', () => {
            // Установка сегодняшней даты по умолчанию в окне записи
            document.getElementById('bookingDate').valueAsDate = new Date();

            saveState();
            updateAdminUI();
            renderHeaderUser();
            renderCatalog();
            loadServicesFromDB();
            loadBookingsFromDB();

            // Закрытие модальных окон по крестику или клику на фон
            document.querySelectorAll('[data-close]').forEach(btn => {
                btn.addEventListener('click', () => closeModal(btn.getAttribute('data-close')));
            });
            document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
                backdrop.addEventListener('click', (e) => {
                    if (e.target === backdrop) backdrop.classList.remove('open');
                });
            });

            // Открытие окон из шапки и баннера
            document.getElementById('openMyBookingsBtn').addEventListener('click', () => {
                renderMyBookingsModal();
                openModal('myBookingsModal');
            });
            document.getElementById('openAddModalBtn').addEventListener('click', () => {
                if (!isAdmin()) {
                    showToast('🔒 Добавление услуг доступно только администратору (логин admin)');
                    return;
                }
                openModal('addServiceModal');
            });
            document.getElementById('heroAddServiceBtn').addEventListener('click', () => {
                if (!isAdmin()) {
                    showToast('🔒 Добавление услуг доступно только администратору (логин admin)');
                    return;
                }
                openModal('addServiceModal');
            });

            // Переключение вкладок Вход / Регистрация
            const tabLoginBtn = document.getElementById('tabLoginBtn');
            const tabRegBtn = document.getElementById('tabRegBtn');
            const loginForm = document.getElementById('loginForm');
            const regForm = document.getElementById('regForm');

            tabLoginBtn.addEventListener('click', () => {
                tabLoginBtn.classList.add('active');
                tabRegBtn.classList.remove('active');
                loginForm.style.display = 'block';
                regForm.style.display = 'none';
            });

            tabRegBtn.addEventListener('click', () => {
                tabRegBtn.classList.add('active');
                tabLoginBtn.classList.remove('active');
                regForm.style.display = 'block';
                loginForm.style.display = 'none';
            });

            // Обработка Регистрации (сохраняется в БД через apiRequest)
            regForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const newUser = {
                    name: document.getElementById('regName').value.trim(),
                    phone: document.getElementById('regPhone').value.trim(),
                    login: document.getElementById('regLogin').value.trim(),
                    password: document.getElementById('regPass').value
                };

                const res = await apiRequest('POST', API_CONFIG.ENDPOINTS.REGISTER, newUser);
                if (!res.ok) { showToast('⚠️ ' + res.error); return; }
                activeUser = res.user; // пользователь уже сохранён в таблице users
                clientBookings = [];
                saveState();
                updateAdminUI();
                renderHeaderUser();
                renderCatalog();
                closeModal('authModal');
                regForm.reset();
                showToast(`🌸 Добро пожаловать в LUMIÈRE, ${newUser.name}!`);
            });

            // Обработка Входа
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const loginVal = document.getElementById('loginInput').value.trim();
                const passVal = document.getElementById('loginPass').value;

                const res = await apiRequest('POST', API_CONFIG.ENDPOINTS.LOGIN, { login: loginVal, password: passVal });
                if (!res.ok) { showToast('⚠️ ' + res.error); return; }
                activeUser = res.user;
                await loadBookingsFromDB();
                saveState();
                updateAdminUI();
                renderHeaderUser();
                renderCatalog();
                closeModal('authModal');
                loginForm.reset();
                if (isAdmin()) {
                    showToast(`👑 Вход выполнен: режим Администратора (добавление услуг активно)`);
                } else {
                    showToast(`✨ Рады видеть вас, ${activeUser.name}!`);
                }
            });

            // Делегирование кликов по карточкам услуг (Записаться / Удалить)
            document.getElementById('servicesGrid').addEventListener('click', (e) => {
                const bookBtn = e.target.closest('[data-book-id]');
                const delBtn = e.target.closest('[data-del-id]');

                if (bookBtn) {
                    const serviceId = Number(bookBtn.getAttribute('data-book-id'));
                    const service = servicesList.find(s => s.id === serviceId);
                    if (!service) return;

                    document.getElementById('bookingServiceId').value = service.id;
                    document.getElementById('bookingServiceName').textContent = `${service.title} — ${service.price.toLocaleString('ru-RU')} ₽`;
                    if (activeUser) {
                        document.getElementById('bookingClientName').value = activeUser.name || '';
                        document.getElementById('bookingClientPhone').value = activeUser.phone || '';
                    }

                    // Настройка программы лояльности в окне записи
                    const cashbackEl = document.getElementById('cashbackAmount');
                    const usePointsSec = document.getElementById('usePointsSection');
                    const usePointsCb = document.getElementById('usePointsCheckbox');
                    const finalPriceEl = document.getElementById('bookingFinalPrice');
                    const discountSummary = document.getElementById('pointsDiscountSummary');
                    const discountVal = document.getElementById('pointsDiscountVal');
                    const availBadge = document.getElementById('availPointsBadge');

                    const updateBookingPrice = () => {
                        let finalPrice = service.price;
                        let discount = 0;
                        if (usePointsCb && usePointsCb.checked && activeUser && activeUser.points > 0) {
                            discount = Math.min(activeUser.points, Math.floor(service.price));
                            finalPrice = Math.max(0, service.price - discount);
                            if (discountSummary) discountSummary.style.display = 'block';
                            if (discountVal) discountVal.textContent = `-${discount.toLocaleString('ru-RU')} ₽`;
                        } else {
                            if (discountSummary) discountSummary.style.display = 'none';
                        }
                        if (finalPriceEl) finalPriceEl.textContent = `${finalPrice.toLocaleString('ru-RU')} ₽`;
                        const cb = Math.max(10, Math.round(finalPrice * 0.05));
                        if (cashbackEl) cashbackEl.textContent = `+${cb} баллов (5%)`;
                    };

                    if (usePointsCb) {
                        usePointsCb.checked = false;
                        usePointsCb.onchange = updateBookingPrice;
                    }

                    if (activeUser && activeUser.points > 0) {
                        if (usePointsSec) usePointsSec.style.display = 'block';
                        if (availBadge) availBadge.textContent = activeUser.points;
                    } else {
                        if (usePointsSec) usePointsSec.style.display = 'none';
                    }

                    updateBookingPrice();
                    openModal('bookingModal');
                }

                if (delBtn) {
                    const serviceId = Number(delBtn.getAttribute('data-del-id'));
                    const target = servicesList.find(s => s.id === serviceId);
                    apiRequest('DELETE', API_CONFIG.ENDPOINTS.SERVICES + '/' + serviceId).then(res => {
                        if (!res.ok) { showToast('⚠️ ' + (res.error || 'Не удалось удалить')); return; }
                        servicesList = servicesList.filter(s => s.id !== serviceId);
                        saveState();
                        renderCatalog();
                        // записи на удалённую услугу удалены в БД каскадно
                        loadBookingsFromDB();
                        if (target) showToast(`Удалено из каталога: «${target.title}»`);
                    });
                }
            });

            // Подтверждение записи на услугу (сохраняется в БД через apiRequest)
            document.getElementById('bookingForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const serviceId = Number(document.getElementById('bookingServiceId').value);
                const service = servicesList.find(s => s.id === serviceId);
                if (!service) return;

                const usePoints = document.getElementById('usePointsCheckbox') ? document.getElementById('usePointsCheckbox').checked : false;

                const res = await apiRequest('POST', API_CONFIG.ENDPOINTS.BOOKINGS, {
                    userId: activeUser ? activeUser.id : null,
                    serviceId: service.id,
                    clientName: document.getElementById('bookingClientName').value.trim(),
                    clientPhone: document.getElementById('bookingClientPhone').value.trim(),
                    master: document.getElementById('bookingMaster').value,
                    date: document.getElementById('bookingDate').value,
                    time: document.getElementById('bookingTime').value,
                    usePoints: usePoints
                });
                if (!res.ok) { showToast('⚠️ ' + res.error); return; }
                const bookingRecord = res.booking;
                clientBookings.unshift(bookingRecord);

                if (activeUser && res.userPoints !== undefined) {
                    activeUser.points = res.userPoints;
                }
                saveState();
                renderHeaderUser();
                closeModal('bookingModal');
                
                const bonusMsg = res.pointsEarned ? ` (Начислено +${res.pointsEarned} баллов 💎)` : '';
                showToast(`💖 Вы записаны: «${service.title}»${bonusMsg}`);
            });

            // Отмена записи в окне "Мои записи"
            document.getElementById('myBookingsList').addEventListener('click', (e) => {
                const cancelBtn = e.target.closest('[data-cancel-booking]');
                if (!cancelBtn) return;
                const bId = Number(cancelBtn.getAttribute('data-cancel-booking'));
                apiRequest('DELETE', API_CONFIG.ENDPOINTS.BOOKINGS + '/' + bId).then(async (res) => {
                    if (!res.ok) { showToast('⚠️ ' + (res.error || 'Не удалось отменить')); return; }
                    clientBookings = clientBookings.filter(b => b.id !== bId);
                    if (activeUser) {
                        const ptsRes = await apiRequest('GET', '/user/points?userId=' + activeUser.id);
                        if (ptsRes.ok) activeUser.points = ptsRes.points;
                    }
                    saveState();
                    renderHeaderUser();
                    renderMyBookingsModal();
                    showToast('Запись отменена (баланс баллов скорректирован)');
                });
            });

            // Добавление новой услуги / товара
            document.getElementById('addServiceForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                if (!isAdmin()) {
                    showToast('🔒 Ошибка: добавлять услуги может только администратор (войдите под логином admin)');
                    return;
                }
                const submitBtn = e.target.querySelector('button[type="submit"]');
                if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Добавление...'; }

                const res = await apiRequest('POST', API_CONFIG.ENDPOINTS.SERVICES, {
                    title: document.getElementById('newTitle').value.trim(),
                    category: document.getElementById('newCat').value,
                    price: Number(document.getElementById('newPrice').value),
                    duration: document.getElementById('newDuration').value.trim(),
                    image: document.getElementById('newImg').value.trim(),
                    emoji: '💇‍♀️',
                    desc: document.getElementById('newDesc').value.trim(),
                    adminLogin: activeUser ? activeUser.login : 'admin'
                });

                if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Добавить на сайт'; }

                if (!res.ok) {
                    showToast('⚠️ ' + (res.error || 'Не удалось добавить услугу'));
                    return;
                }
                const newItem = { ...res.service, desc: res.service.desc || '', duration: res.service.duration || '' };
                servicesList.unshift(newItem);
                saveState();
                renderCatalog();
                closeModal('addServiceModal');
                e.target.reset();
                showToast(`✨ Услуга успешно добавлена: «${newItem.title}»`);
            });

            // -------------------------------------------------------------
            // Массовый перерасчет цен в MySQL (Версия 4)
            // -------------------------------------------------------------
            const maxThresholdInput = document.getElementById('recalcMaxThreshold');
            const newPriceInput = document.getElementById('recalcNewPrice');
            const minThresholdInput = document.getElementById('recalcMinThreshold');
            const sqlPreviewCode = document.getElementById('sqlPreviewCode');
            const affectedCountEl = document.getElementById('affectedServicesCount');

            function updateRecalcPreview() {
                const maxT = Number(maxThresholdInput ? maxThresholdInput.value : 0) || 0;
                const newP = Number(newPriceInput ? newPriceInput.value : 0) || 0;
                const minT = minThresholdInput && minThresholdInput.value ? Number(minThresholdInput.value) : 0;

                const matching = servicesList.filter(s => {
                    if (minT > 0) return s.price >= minT && s.price < maxT;
                    return s.price < maxT;
                });
                if (affectedCountEl) affectedCountEl.textContent = matching.length;

                let sql = '';
                if (minT > 0) {
                    sql = `UPDATE services SET price = ${newP.toFixed(2)} WHERE price >= ${minT.toFixed(2)} AND price < ${maxT.toFixed(2)};`;
                } else {
                    sql = `UPDATE services SET price = ${newP.toFixed(2)} WHERE price < ${maxT.toFixed(2)};`;
                }
                if (sqlPreviewCode) sqlPreviewCode.textContent = sql;
            }

            const openRecalcHandler = () => {
                if (!isAdmin()) {
                    showToast('🔒 Перерасчет цен доступен только администратору (логин admin)');
                    return;
                }
                updateRecalcPreview();
                openModal('recalcModal');
            };

            const openRecalcBtn = document.getElementById('openRecalcModalBtn');
            const heroRecalcBtn = document.getElementById('heroRecalcBtn');
            if (openRecalcBtn) openRecalcBtn.addEventListener('click', openRecalcHandler);
            if (heroRecalcBtn) heroRecalcBtn.addEventListener('click', openRecalcHandler);

            [maxThresholdInput, newPriceInput, minThresholdInput].forEach(inp => {
                if (inp) inp.addEventListener('input', updateRecalcPreview);
            });

            document.querySelectorAll('.preset-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const t = btn.getAttribute('data-threshold');
                    const n = btn.getAttribute('data-new');
                    if (t && maxThresholdInput) maxThresholdInput.value = t;
                    if (n && newPriceInput) newPriceInput.value = n;
                    if (minThresholdInput) minThresholdInput.value = '';
                    updateRecalcPreview();
                });
            });

            const copySqlBtn = document.getElementById('copySqlBtn');
            if (copySqlBtn) {
                copySqlBtn.addEventListener('click', () => {
                    const text = sqlPreviewCode ? sqlPreviewCode.textContent : '';
                    if (navigator.clipboard && text) {
                        navigator.clipboard.writeText(text).then(() => {
                            showToast('📋 SQL-запрос скопирован в буфер обмена!');
                        });
                    }
                });
            }

            const recalcForm = document.getElementById('recalcForm');
            if (recalcForm) {
                recalcForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    if (!isAdmin()) {
                        showToast('🔒 Ошибка: выполнять перерасчет может только администратор');
                        return;
                    }

                    const submitBtn = document.getElementById('submitRecalcBtn');
                    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Выполнение SQL в MySQL...'; }

                    const maxThreshold = Number(maxThresholdInput.value);
                    const newPrice = Number(newPriceInput.value);
                    const minThreshold = minThresholdInput.value ? Number(minThresholdInput.value) : null;

                    const res = await apiRequest('POST', API_CONFIG.ENDPOINTS.RECALCULATE, {
                        maxThreshold,
                        newPrice,
                        minThreshold,
                        adminLogin: activeUser ? activeUser.login : 'admin'
                    });

                    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = '⚡ Выполнить перерасчет в MySQL'; }

                    if (!res.ok) {
                        showToast('⚠️ ' + (res.error || 'Ошибка перерасчета цен'));
                        return;
                    }

                    if (Array.isArray(res.services)) {
                        servicesList = res.services.map(s => ({
                            ...s,
                            desc: s.desc || '',
                            duration: s.duration || ''
                        }));
                        saveState();
                        renderCatalog();
                    }

                    closeModal('recalcModal');
                    showToast(`🎉 ${res.message || 'Цены успешно обновлены в MySQL!'}`);
                });
            }

            // Фильтры, поиск и ползунок цены
            document.getElementById('searchField').addEventListener('input', renderCatalog);
            document.getElementById('sortOrder').addEventListener('change', renderCatalog);
            document.getElementById('priceRange').addEventListener('input', (e) => {
                document.getElementById('priceLabel').textContent = Number(e.target.value).toLocaleString('ru-RU') + ' ₽';
                renderCatalog();
            });

            document.querySelectorAll('#categoryTabs .tab-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('#categoryTabs .tab-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    activeCategory = btn.getAttribute('data-cat');
                    renderCatalog();
                });
            });

            // Переключение цветовой палитры (ТЗ: Задать стиль / цвет)
            document.querySelectorAll('.color-dot').forEach(dot => {
                dot.addEventListener('click', () => {
                    document.documentElement.removeAttribute('style');
                    document.querySelectorAll('.color-dot').forEach(d => d.classList.remove('active'));
                    dot.classList.add('active');
                    const theme = dot.getAttribute('data-theme-val');
                    if (theme === 'default') {
                        document.documentElement.removeAttribute('data-theme');
                    } else {
                        document.documentElement.setAttribute('data-theme', theme);
                    }
                    showToast('🎨 Цветовое оформление обновлено');
                });
            });

            document.getElementById('customColorInput').addEventListener('input', (e) => {
                const hex = e.target.value;
                document.querySelectorAll('.color-dot').forEach(d => d.classList.remove('active'));
                document.documentElement.style.setProperty('--accent', hex);
                document.documentElement.style.setProperty('--accent-hover', hex);
                document.documentElement.style.setProperty('--accent-glow', hex + '66');
                document.documentElement.style.setProperty('--accent-soft', hex + '22');
            });
        });
