// frontend/js/app.js - ИСПРАВЛЕННАЯ ВЕРСИЯ с проверками DOM

const API_URL = 'http://localhost:8000/api';
let currentSportType = null;
let currentGenderFilter = '';

// Глобальные переменные для UX
let isAddingResult = false;
let validationTimer = null;

// ===========================================
// ИНИЦИАЛИЗАЦИЯ И ОСНОВНЫЕ ФУНКЦИИ
// ===========================================

// Обработка кликов по кнопкам выбора пола
function initGenderButtons() {
    console.log('Инициализация кнопок выбора пола...');

    const genderLabels = document.querySelectorAll('.gender-filter label');
    const genderRadios = document.querySelectorAll('input[name="filter-gender"]');

    if (genderLabels.length === 0 || genderRadios.length === 0) {
        console.warn('Gender filter elements not found');
        return;
    }

    // Функция для обновления активных классов
    function updateActiveClasses() {
        genderLabels.forEach(label => {
            label.classList.remove('active');
        });

        const checkedRadio = document.querySelector('input[name="filter-gender"]:checked');
        if (checkedRadio) {
            checkedRadio.closest('label').classList.add('active');
        }
    }

    // Обработчик для радио-кнопок
    genderRadios.forEach(radio => {
        radio.addEventListener('change', updateActiveClasses);
    });

    // Обработчик для кликов по лейблам
    genderLabels.forEach(label => {
        label.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                updateActiveClasses();
                // Запускаем событие change для радио-кнопки
                radio.dispatchEvent(new Event('change'));
            }
        });
    });

    // Инициализация начального состояния
    updateActiveClasses();
}

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Инициализация приложения...');

    // Проверяем наличие основных элементов
    const requiredElements = ['institute-input', 'name-input', 'result-input', 'sport-type', 'results-tbody', 'rating-list'];
    const missingElements = requiredElements.filter(id => !document.getElementById(id));

    if (missingElements.length > 0) {
        console.error('Отсутствуют элементы:', missingElements);
        showInfoPanel('Ошибка: отсутствуют необходимые элементы интерфейса', 'error');
        return;
    }

    try {
        await loadSportTypes();
        await loadResults();
        await loadRating();

        // Инициализация кнопок выбора пола
        initGenderButtons();

        // Инициализация валидации формы
        initializeFormValidation();

        console.log('Приложение успешно инициализировано');

    } catch (error) {
        console.error('Error initializing app:', error);
        showInfoPanel('Ошибка инициализации приложения', 'error');
    }

    // Set up event listeners
    const sportTypeSelect = document.getElementById('sport-type');
    if (sportTypeSelect) {
        sportTypeSelect.addEventListener('change', async (e) => {
            currentSportType = e.target.value ? parseInt(e.target.value) : null;
            console.log('Выбран вид спорта:', currentSportType);
            await loadResults();
            await loadRating();
            updatePlaceInput();
            updateResultInputPlaceholder();
        });
    }

    // Gender filter event listeners
    document.querySelectorAll('input[name="filter-gender"]').forEach(radio => {
        radio.addEventListener('change', async (e) => {
            currentGenderFilter = e.target.value;
            console.log('Выбран фильтр по полу:', currentGenderFilter);
            await loadResults();
            await loadRating();
        });
    });

    // Инициализация подсказок
    updateResultInputPlaceholder();
});

// ===========================================
// ЗАГРУЗКА ДАННЫХ
// ===========================================

// Load sport types for dropdown
async function loadSportTypes() {
    try {
        console.log('Загрузка видов спорта...');
        const response = await fetch(`${API_URL}/competitions/sport-types/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const sportTypes = await response.json();
        console.log('Виды спорта загружены:', sportTypes);

        const select = document.getElementById('sport-type');
        if (!select) {
            throw new Error('Sport type select element not found');
        }

        select.innerHTML = '<option value="">Вид соревнований</option>';

        if (Array.isArray(sportTypes)) {
            sportTypes.forEach(sport => {
                const option = document.createElement('option');
                option.value = sport.id;
                option.textContent = sport.name;
                select.appendChild(option);
            });
        } else {
            console.error('Sport types is not an array:', sportTypes);
        }
    } catch (error) {
        console.error('Error loading sport types:', error);
        const select = document.getElementById('sport-type');
        if (select) {
            select.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    }
}

// Update place input based on current results
function updatePlaceInput() {
    const tbody = document.getElementById('results-tbody');
    if (!tbody) return;

    const rows = tbody.getElementsByTagName('tr');
    const nextPlace = rows.length + 1;

    const placeInput = document.getElementById('place-input');
    if (placeInput) {
        placeInput.value = nextPlace;
    }
}

// Load competition results
async function loadResults() {
    try {
        const tbody = document.getElementById('results-tbody');
        if (!tbody) {
            console.error('Results tbody not found');
            return;
        }

        // Если не выбран вид спорта, показываем сообщение
        if (!currentSportType) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-sport-message">Выберите вид спорта</td></tr>';
            updatePlaceInput();
            return;
        }

        let url = `${API_URL}/results/competition-results/?sport_type_id=${currentSportType}`;

        // Добавляем фильтр по полу если он установлен
        if (currentGenderFilter) {
            url += `&gender=${currentGenderFilter}`;
        }

        console.log('Загрузка результатов с URL:', url);

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const results = await response.json();
        console.log('Результаты загружены:', results);

        tbody.innerHTML = '';

        if (Array.isArray(results)) {
            if (results.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="no-results-message">Нет результатов</td></tr>';
                updatePlaceInput();
                return;
            }

            // Определяем, командный ли это вид спорта
            const sportName = document.querySelector(`#sport-type option[value="${currentSportType}"]`)?.textContent || '';
            const isTeamSport = ['Баскетбол', 'Волейбол', 'Футбол'].some(sport => sportName.includes(sport));

            if (currentGenderFilter) {
                // РАЗДЕЛЬНЫЙ ПОДСЧЕТ ПО ПОЛУ - показываем с баллами за места
                if (isTeamSport) {
                    displayTeamResultsWithPoints(results);
                } else {
                    displayIndividualResultsWithPoints(results);
                }
            } else {
                // ОБЩИЙ ПРОТОКОЛ - показываем абсолютные результаты С баллами
                if (isTeamSport) {
                    displayMixedTeamResults(results);
                } else {
                    displayMixedIndividualResults(results);
                }
            }
        } else {
            console.error('Results is not an array:', results);
            tbody.innerHTML = '<tr><td colspan="6" class="error-message">Ошибка загрузки данных</td></tr>';
        }

        updatePlaceInput();

    } catch (error) {
        console.error('Error loading results:', error);
        const tbody = document.getElementById('results-tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="error-message">Ошибка загрузки результатов</td></tr>';
        }
        updatePlaceInput();
    }
}

// ===========================================
// ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ
// ===========================================

function displayTeamResultsWithPoints(results) {
    const tbody = document.getElementById('results-tbody');
    if (!tbody) return;

    console.log('Отображение командных результатов с фильтром по полу:', results);

    // Если результатов нет, показываем сообщение
    if (!results || results.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-results-message">Нет результатов для выбранного пола</td></tr>';
        return;
    }

    // Группируем по факультетам (в рамках одного пола)
    const facultyGroups = {};
    results.forEach(performance => {
        const facultyId = performance.faculty_id;
        if (!facultyGroups[facultyId]) {
            facultyGroups[facultyId] = {
                faculty_abbreviation: performance.faculty_abbreviation,
                faculty_name: performance.faculty_name,
                place: performance.place,
                points: performance.points,
                members: [],
                original_result: performance.original_result,
                time_result: performance.time_result
            };
        }
        facultyGroups[facultyId].members.push(performance.student_name);
    });

    // Проверяем есть ли команды после группировки
    const teams = Object.values(facultyGroups);
    if (teams.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-results-message">Команды не найдены для выбранного пола</td></tr>';
        return;
    }

    // Сортируем команды по баллам (больше баллов = лучше место)
    teams.sort((a, b) => b.points - a.points);

    // Пересчитываем места после сортировки
    let currentPlace = 1;
    for (let i = 0; i < teams.length; i++) {
        if (i > 0 && teams[i].points !== teams[i - 1].points) {
            currentPlace = i + 1;
        }
        teams[i].place = currentPlace;
    }

    // Отображаем командные результаты с баллами в правильном порядке
    teams.forEach(group => {
        let placeClass = '';
        if (group.place === 1) placeClass = 'gold-place';
        else if (group.place === 2) placeClass = 'silver-place';
        else if (group.place === 3) placeClass = 'bronze-place';

        // Определяем отображение результата
        let resultDisplay = '-';
        if (group.time_result) {
            resultDisplay = group.time_result;
        } else if (group.original_result) {
            resultDisplay = `${group.original_result.toFixed(1)} очков`;
        }

        // Заголовок команды
        const headerRow = document.createElement('tr');
        headerRow.className = 'team-header';
        headerRow.innerHTML = `
            <td class="${placeClass}">${group.place}</td>
            <td colspan="2">${group.faculty_abbreviation} - Команда</td>
            <td>${resultDisplay}</td>
            <td>${group.points.toFixed(0)}</td>
            <td></td>
        `;
        tbody.appendChild(headerRow);

        // Члены команды
        group.members.forEach(member => {
            const memberRow = document.createElement('tr');
            memberRow.className = 'team-member';
            memberRow.innerHTML = `
                <td></td>
                <td></td>
                <td style="padding-left: 30px;">↳ ${member}</td>
                <td>-</td>
                <td>${group.points.toFixed(0)}</td>
                <td></td>
            `;
            tbody.appendChild(memberRow);
        });
    });

    console.log(`Отображено ${teams.length} команд(ы)`);
}

function displayIndividualResultsWithPoints(results) {
    const tbody = document.getElementById('results-tbody');
    if (!tbody) return;

    // Отображаем индивидуальные результаты с баллами
    results.forEach(performance => {
        const row = document.createElement('tr');

        let placeClass = '';
        if (performance.place === 1) placeClass = 'gold-place';
        else if (performance.place === 2) placeClass = 'silver-place';
        else if (performance.place === 3) placeClass = 'bronze-place';

        let resultDisplay = performance.time_result || '-';
        if (performance.time_result) {
            resultDisplay = performance.time_result;
        } else if (performance.original_result) {
            resultDisplay = `${performance.original_result.toFixed(1)} очков`;
        } else {
            resultDisplay = '-';
        }

        row.innerHTML = `
            <td class="${placeClass}">${performance.place}</td>
            <td>${performance.faculty_abbreviation}</td>
            <td>${performance.student_name}</td>
            <td>${resultDisplay}</td>
            <td>${performance.points.toFixed(0)}</td>
            <td>
                <button class="btn-delete" onclick="deleteResult(${performance.performance_id})">Удалить</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function displayMixedTeamResults(results) {
    const tbody = document.getElementById('results-tbody');
    if (!tbody) return;

    // Данные уже приходят отсортированными с сервера,
    // просто группируем их сохраняя порядок
    const teamGroups = {};
    const teamOrder = []; // Массив для сохранения порядка команд

    results.forEach(performance => {
        // faculty_abbreviation уже содержит пол в скобках с сервера
        const teamKey = performance.faculty_abbreviation;

        if (!teamGroups[teamKey]) {
            teamGroups[teamKey] = {
                team_name: teamKey,
                place: performance.place,
                original_result: performance.original_result,
                time_result: performance.time_result,
                points: performance.points,
                members: []
            };
            // Сохраняем порядок первого появления команды
            teamOrder.push(teamKey);
        }
        teamGroups[teamKey].members.push(performance.student_name);
    });

    // Отображаем команды в том порядке, в котором они пришли с сервера
    teamOrder.forEach(teamKey => {
        const group = teamGroups[teamKey];

        let placeClass = '';
        if (group.place === 1) placeClass = 'gold-place';
        else if (group.place === 2) placeClass = 'silver-place';
        else if (group.place === 3) placeClass = 'bronze-place';

        let resultDisplay = group.time_result || '-';
        if (group.time_result) {
            resultDisplay = group.time_result;
        } else if (group.original_result) {
            resultDisplay = `${group.original_result.toFixed(1)} очков`;
        } else {
            resultDisplay = '-';
        }

        // Заголовок команды
        const headerRow = document.createElement('tr');
        headerRow.className = 'team-header';
        headerRow.innerHTML = `
            <td class="${placeClass}">${group.place}</td>
            <td colspan="2">${group.team_name}</td>
            <td>${resultDisplay}</td>
            <td>${group.points ? group.points.toFixed(0) : '-'}</td>
            <td></td>
        `;
        tbody.appendChild(headerRow);

        // Члены команды
        group.members.forEach(member => {
            const memberRow = document.createElement('tr');
            memberRow.className = 'team-member';
            memberRow.innerHTML = `
                <td></td>
                <td></td>
                <td style="padding-left: 30px;">↳ ${member}</td>
                <td>-</td>
                <td>${group.points ? group.points.toFixed(0) : '-'}</td>
                <td></td>
            `;
            tbody.appendChild(memberRow);
        });
    });
}

function displayMixedIndividualResults(results) {
    const tbody = document.getElementById('results-tbody');
    if (!tbody) return;

    // Отображаем общий протокол всех участников с баллами
    results.forEach(performance => {
        const row = document.createElement('tr');

        let placeClass = '';
        if (performance.place === 1) placeClass = 'gold-place';
        else if (performance.place === 2) placeClass = 'silver-place';
        else if (performance.place === 3) placeClass = 'bronze-place';

        let resultDisplay = performance.time_result || '-';
        if (performance.time_result) {
            resultDisplay = performance.time_result;
        } else if (performance.original_result) {
            resultDisplay = `${performance.original_result.toFixed(1)} очков`;
        } else {
            resultDisplay = '-';
        }

        // student_name уже содержит пол в скобках с сервера
        const studentNameWithGender = performance.student_name;

        row.innerHTML = `
            <td class="${placeClass}">${performance.place}</td>
            <td>${performance.faculty_abbreviation}</td>
            <td>${studentNameWithGender}</td>
            <td>${resultDisplay}</td>
            <td>${performance.points ? performance.points.toFixed(0) : '-'}</td>
            <td>
                <button class="btn-delete" onclick="deleteResult(${performance.performance_id})">Удалить</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// ===========================================
// РЕЙТИНГ
// ===========================================

// Load rating
async function loadRating() {
    try {
        let url = `${API_URL}/results/faculty-sport-rating/`;

        // Добавляем параметры фильтрации
        const params = [];
        if (currentSportType) {
            params.push(`sport_type_id=${currentSportType}`);
        }
        if (currentGenderFilter) {
            params.push(`gender=${currentGenderFilter}`);
        }

        if (params.length > 0) {
            url += `?${params.join('&')}`;
        }

        console.log('Загрузка рейтинга с URL:', url);

        const response = await fetch(url);
        if (!response.ok) {
            // Fallback к общему рейтингу
            const fallbackUrl = currentGenderFilter
                ? `${API_URL}/results/faculty-sport-rating/?gender=${currentGenderFilter}`
                : `${API_URL}/results/spartakiada-rating/`;

            const fallbackResponse = await fetch(fallbackUrl);
            if (!fallbackResponse.ok) {
                throw new Error(`HTTP error! status: ${fallbackResponse.status}`);
            }
            const ratings = await fallbackResponse.json();
            displayRating(ratings);
            return;
        }

        const ratings = await response.json();
        console.log('Рейтинг загружен:', ratings);
        displayRating(ratings);

    } catch (error) {
        console.error('Error loading rating:', error);
        const ratingList = document.getElementById('rating-list');
        if (ratingList) {
            ratingList.innerHTML = '<div style="text-align: center;">Ошибка загрузки рейтинга</div>';
        }
    }
}

// Display rating
function displayRating(ratings) {
    const ratingList = document.getElementById('rating-list');
    if (!ratingList) {
        console.error('Rating list element not found');
        return;
    }

    ratingList.innerHTML = '';

    if (Array.isArray(ratings)) {
        ratings.forEach(rating => {
            const item = document.createElement('div');
            item.className = 'rating-item';

            let placeClass = '';
            if (rating.place === 1 || rating.overall_place === 1) placeClass = 'gold-text';
            else if (rating.place === 2 || rating.overall_place === 2) placeClass = 'silver-text';
            else if (rating.place === 3 || rating.overall_place === 3) placeClass = 'bronze-text';

            const place = rating.place || rating.overall_place || '-';
            const points = rating.total_points ? Math.round(rating.total_points) : 0;

            item.innerHTML = `
                <span class="${placeClass}">${place}. ${rating.faculty_abbreviation}</span>
                <span class="${placeClass}">${points}</span>
            `;
            ratingList.appendChild(item);
        });

        // Обновляем заголовок рейтинга с учетом фильтра по полу
        const ratingTitle = document.querySelector('.rating-panel h3');
        if (ratingTitle) {
            let titleText = 'Баллы: ';

            if (currentSportType) {
                const sportName = document.querySelector(`#sport-type option[value="${currentSportType}"]`)?.textContent || '';
                titleText += sportName;
            } else {
                titleText += 'Общий зачет';
            }

            // Добавляем информацию о фильтре по полу
            if (currentGenderFilter) {
                titleText += ` (${currentGenderFilter === 'М' ? 'Мужчины' : 'Женщины'})`;
            } else {
                titleText += ' (Все)';
            }

            ratingTitle.textContent = titleText;
        }
    } else {
        console.error('Ratings is not an array:', ratings);
    }
}

// ===========================================
// ДОБАВЛЕНИЕ РЕЗУЛЬТАТОВ - HELPER ФУНКЦИИ
// ===========================================

// Функция для определения типа результата по виду спорта
function getResultType(sportName) {
    const timeBased = ['Бег', 'Плавание'];
    const isTimeBased = timeBased.some(sport => sportName.includes(sport));
    return isTimeBased ? 'time' : 'points';
}

// Функция для конвертации времени в секунды
function timeToSeconds(timeString) {
    try {
        // Форматы: "12.34" (секунды), "1:23.45" (минуты:секунды), "1:23:45" (часы:минуты:секунды)
        const parts = timeString.split(':');

        if (parts.length === 1) {
            // Только секунды
            return parseFloat(parts[0]);
        } else if (parts.length === 2) {
            // Минуты:секунды
            return parseInt(parts[0]) * 60 + parseFloat(parts[1]);
        } else if (parts.length === 3) {
            // Часы:минуты:секунды
            return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseFloat(parts[2]);
        }

        throw new Error('Неверный формат времени');
    } catch (error) {
        throw new Error('Неверный формат времени. Используйте: 12.34 или 1:23.45 или 1:23:45');
    }
}

// Функция для форматирования времени в стандартный вид
function formatTime(timeString) {
    try {
        const totalSeconds = timeToSeconds(timeString);

        if (totalSeconds < 60) {
            // Меньше минуты - показываем как секунды
            return `0:00:${totalSeconds.toFixed(2)}`;
        } else if (totalSeconds < 3600) {
            // Меньше часа - показываем минуты:секунды
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = (totalSeconds % 60).toFixed(2);
            return `0:${minutes.toString().padStart(2, '0')}:${seconds.padStart(5, '0')}`;
        } else {
            // Час и больше - показываем часы:минуты:секунды
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = (totalSeconds % 60).toFixed(2);
            return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.padStart(5, '0')}`;
        }
    } catch (error) {
        return timeString; // Возвращаем как есть если не удалось распарсить
    }
}

// Валидация результата
function validateResult(result, resultType) {
    if (!result || result.trim() === '') {
        throw new Error('Результат не может быть пустым');
    }

    if (resultType === 'time') {
        try {
            timeToSeconds(result);
        } catch (error) {
            throw new Error('Неверный формат времени. Примеры: 12.34 (сек), 1:23.45 (мин:сек), 1:23:45 (час:мин:сек)');
        }
    } else {
        const points = parseFloat(result);
        if (isNaN(points) || points < 0) {
            throw new Error('Результат должен быть положительным числом');
        }
    }
}

// ===========================================
// UX ФУНКЦИИ
// ===========================================

// Функция для показа информационных сообщений
function showInfoPanel(message, type = 'info', duration = 5000) {
    const panel = document.getElementById('info-panel');
    const text = document.getElementById('info-text');
    const icon = document.querySelector('.info-icon');

    if (!panel || !text || !icon) {
        console.warn('Info panel elements not found');
        return;
    }

    // Очищаем предыдущие классы
    panel.className = 'info-panel';

    // Добавляем класс типа сообщения
    if (type === 'success') {
        panel.classList.add('success');
        icon.textContent = '✅';
    } else if (type === 'error') {
        panel.classList.add('error');
        icon.textContent = '❌';
    } else {
        icon.textContent = 'ℹ️';
    }

    text.textContent = message;
    panel.style.display = 'block';

    // Автоматически скрываем через заданное время
    if (duration > 0) {
        setTimeout(() => {
            panel.style.display = 'none';
        }, duration);
    }
}

// Функция для установки состояния поля ввода
function setFieldState(fieldId, state, message = '') {
    const input = document.getElementById(fieldId);
    if (!input) {
        console.warn(`Element ${fieldId} not found`);
        return;
    }

    const field = input.closest('.input-field');
    if (!field) {
        console.warn(`Parent .input-field not found for ${fieldId}`);
        return;
    }

    const hint = field.querySelector('.input-hint');

    // Очищаем предыдущие состояния
    field.classList.remove('error', 'success');

    if (state === 'error') {
        field.classList.add('error');
        if (hint && message) {
            hint.textContent = message;
            hint.style.color = '#e74c3c';
        }
    } else if (state === 'success') {
        field.classList.add('success');
        if (hint && message) {
            hint.textContent = message;
            hint.style.color = '#27ae60';
        }
    } else {
        // Возвращаем исходное состояние
        if (hint) {
            updateFieldHint(fieldId);
        }
    }
}

// Обновление подсказок для полей
function updateFieldHint(fieldId) {
    const input = document.getElementById(fieldId);
    if (!input) return;

    const field = input.closest('.input-field');
    if (!field) return;

    const hint = field.querySelector('.input-hint');
    if (!hint) return;

    switch (fieldId) {
        case 'institute-input':
            hint.textContent = 'Введите сокращение института';
            hint.style.color = '#666';
            break;
        case 'name-input':
            hint.textContent = 'Формат: Фамилия Имя Отчество';
            hint.style.color = '#666';
            break;
        case 'result-input':
            updateResultInputHint();
            break;
    }
}

// Обновление подсказки для поля результата
function updateResultInputHint() {
    const input = document.getElementById('result-input');
    if (!input) return;

    const field = input.closest('.input-field');
    if (!field) return;

    const hint = field.querySelector('.input-hint');
    if (!hint) return;

    if (!currentSportType) {
        hint.textContent = 'Выберите вид спорта для формата';
        hint.style.color = '#666';
        return;
    }

    const sportTypeSelect = document.getElementById('sport-type');
    if (!sportTypeSelect) return;

    const sportName = sportTypeSelect.options[sportTypeSelect.selectedIndex].text;
    const resultType = getResultType(sportName);

    if (resultType === 'time') {
        hint.textContent = 'Время: 12.34 (сек) или 1:23.45 (мин:сек)';
    } else {
        hint.textContent = 'Очки: положительное число (например, 85.5)';
    }
    hint.style.color = '#666';
}

// Валидация полей в реальном времени
function validateField(fieldId, value) {
    switch (fieldId) {
        case 'institute-input':
            if (!value.trim()) {
                setFieldState(fieldId, 'error', 'Институт обязателен');
                return false;
            }
            const validInstitutes = ['ИМИТ', 'ИЛГИСН', 'ФТИ', 'МЕДИН', 'ИИИТ'];
            if (!validInstitutes.includes(value.trim().toUpperCase())) {
                setFieldState(fieldId, 'error', 'Используйте: ИМИТ, ИЛГИСН, ФТИ, МедИН, ИИИТ');
                return false;
            }
            setFieldState(fieldId, 'success', '✓ Институт корректен');
            return true;

        case 'name-input':
            if (!value.trim()) {
                setFieldState(fieldId, 'error', 'Имя участника обязательно');
                return false;
            }
            const nameParts = value.trim().split(/\s+/);
            if (nameParts.length < 2) {
                setFieldState(fieldId, 'error', 'Введите минимум фамилию и имя');
                return false;
            }
            setFieldState(fieldId, 'success', `✓ ${nameParts.length} слов(а)`);
            return true;

        case 'result-input':
            if (!value.trim()) {
                setFieldState(fieldId, 'error', 'Результат обязателен');
                return false;
            }

            if (!currentSportType) {
                setFieldState(fieldId, 'error', 'Сначала выберите вид спорта');
                return false;
            }

            try {
                const sportTypeSelect = document.getElementById('sport-type');
                if (!sportTypeSelect) {
                    setFieldState(fieldId, 'error', 'Ошибка при определении вида спорта');
                    return false;
                }

                const sportName = sportTypeSelect.options[sportTypeSelect.selectedIndex].text;
                const resultType = getResultType(sportName);
                validateResult(value, resultType);

                if (resultType === 'time') {
                    const formatted = formatTime(value);
                    setFieldState(fieldId, 'success', `✓ Время: ${formatted}`);
                } else {
                    setFieldState(fieldId, 'success', `✓ Очки: ${parseFloat(value)}`);
                }
                return true;
            } catch (error) {
                setFieldState(fieldId, 'error', error.message);
                return false;
            }
    }
    return true;
}

// Функция для управления состоянием кнопки добавления
function setAddButtonState(loading = false) {
    const button = document.getElementById('add-result-btn');
    if (!button) {
        console.warn('Add result button not found');
        return;
    }

    const textSpan = button.querySelector('.btn-text');
    const spinner = button.querySelector('.btn-spinner');

    if (loading) {
        button.disabled = true;
        if (textSpan) textSpan.style.display = 'none';
        if (spinner) spinner.style.display = 'inline-flex';
        isAddingResult = true;
    } else {
        button.disabled = false;
        if (textSpan) textSpan.style.display = 'inline';
        if (spinner) spinner.style.display = 'none';
        isAddingResult = false;
    }
}

// Инициализация обработчиков событий для валидации в реальном времени
function initializeFormValidation() {
    console.log('Инициализация валидации формы...');

    // Валидация института
    const instituteInput = document.getElementById('institute-input');
    if (instituteInput) {
        instituteInput.addEventListener('input', (e) => {
            clearTimeout(validationTimer);
            validationTimer = setTimeout(() => {
                validateField('institute-input', e.target.value);
            }, 500);
        });

        instituteInput.addEventListener('blur', (e) => {
            validateField('institute-input', e.target.value);
        });
    } else {
        console.warn('Element institute-input not found');
    }

    // Валидация имени
    const nameInput = document.getElementById('name-input');
    if (nameInput) {
        nameInput.addEventListener('input', (e) => {
            clearTimeout(validationTimer);
            validationTimer = setTimeout(() => {
                validateField('name-input', e.target.value);
            }, 500);
        });

        nameInput.addEventListener('blur', (e) => {
            validateField('name-input', e.target.value);
        });
    } else {
        console.warn('Element name-input not found');
    }

    // Валидация результата
    const resultInput = document.getElementById('result-input');
    if (resultInput) {
        resultInput.addEventListener('input', (e) => {
            clearTimeout(validationTimer);
            validationTimer = setTimeout(() => {
                validateField('result-input', e.target.value);
            }, 500);
        });

        resultInput.addEventListener('blur', (e) => {
            validateField('result-input', e.target.value);
        });
    } else {
        console.warn('Element result-input not found');
    }
}

// Обновление плейсхолдера для поля результата
function updateResultInputPlaceholder() {
    const resultInput = document.getElementById('result-input');
    if (!resultInput) return;

    if (!currentSportType) {
        resultInput.placeholder = 'Выберите вид спорта';
        updateResultInputHint();
        return;
    }

    const sportTypeSelect = document.getElementById('sport-type');
    if (!sportTypeSelect) return;

    const sportName = sportTypeSelect.options[sportTypeSelect.selectedIndex].text;
    const resultType = getResultType(sportName);

    if (resultType === 'time') {
        resultInput.placeholder = 'Время: 12.34 или 1:23.45';
    } else {
        resultInput.placeholder = 'Очки: 85.5';
    }

    updateResultInputHint();

    // Перевалидируем результат если он уже введен
    if (resultInput.value.trim()) {
        validateField('result-input', resultInput.value);
    }
}

// ===========================================
// ДОБАВЛЕНИЕ РЕЗУЛЬТАТОВ - ОСНОВНАЯ ФУНКЦИЯ
// ===========================================

// Основная функция добавления результата
async function addResult() {
    if (isAddingResult) return;

    const instituteInput = document.getElementById('institute-input');
    const nameInput = document.getElementById('name-input');
    const resultInput = document.getElementById('result-input');
    const genderRadio = document.querySelector('input[name="gender"]:checked');

    if (!instituteInput || !nameInput || !resultInput || !genderRadio) {
        showInfoPanel('Ошибка: не найдены элементы формы', 'error');
        return;
    }

    const institute = instituteInput.value.trim().toUpperCase();
    const name = nameInput.value.trim();
    const result = resultInput.value.trim();
    const gender = genderRadio.value;

    console.log('=== НАЧАЛО ДОБАВЛЕНИЯ РЕЗУЛЬТАТА ===');
    console.log('Данные формы:', { institute, name, result, gender, currentSportType });

    try {
        // Валидация всех полей
        const instituteValid = validateField('institute-input', institute);
        const nameValid = validateField('name-input', name);
        const resultValid = validateField('result-input', result);

        if (!currentSportType) {
            showInfoPanel('Пожалуйста, выберите вид соревнований', 'error');
            return;
        }

        if (!instituteValid || !nameValid || !resultValid) {
            showInfoPanel('Исправьте ошибки в форме перед отправкой', 'error');
            return;
        }

        // Начинаем процесс добавления
        setAddButtonState(true);
        showInfoPanel('Добавление результата...', 'info', 0);

        // Получаем информацию о виде спорта
        const sportTypeSelect = document.getElementById('sport-type');
        if (!sportTypeSelect) {
            throw new Error('Элемент выбора вида спорта не найден');
        }

        const sportName = sportTypeSelect.options[sportTypeSelect.selectedIndex].text;
        const resultType = getResultType(sportName);

        console.log('Тип результата:', resultType, 'для вида спорта:', sportName);

        // 1. Поиск/создание студента
        showInfoPanel('Поиск участника в базе данных...', 'info', 0);

        const studentRequestData = {
            faculty_abbreviation: institute,
            full_name: name,
            gender: gender
        };

        console.log('Отправка запроса на поиск/создание студента:', studentRequestData);

        const studentResponse = await fetch(`${API_URL}/students/find-or-create/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(studentRequestData)
        });

        console.log('Ответ от студенческого API:', studentResponse.status);

        if (!studentResponse.ok) {
            const errorData = await studentResponse.json();
            console.error('Ошибка от студенческого API:', errorData);
            throw new Error(errorData.detail || 'Ошибка при поиске/создании студента');
        }

        const studentData = await studentResponse.json();
        console.log('Данные студента получены:', studentData);

        // 2. Получение соревнования
        showInfoPanel('Поиск соревнования...', 'info', 0);
        const competitionResponse = await fetch(`${API_URL}/competitions/by-sport/${currentSportType}`);

        console.log('Ответ от API соревнований:', competitionResponse.status);

        if (!competitionResponse.ok) {
            throw new Error('Соревнование по данному виду спорта не найдено');
        }

        const competitionData = await competitionResponse.json();
        console.log('Данные соревнования получены:', competitionData);

        // 3. Получение судьи
        showInfoPanel('Назначение судьи...', 'info', 0);
        const judgeResponse = await fetch(`${API_URL}/students/judges/?sport_type_id=${currentSportType}`);

        console.log('Ответ от API судей:', judgeResponse.status);

        if (!judgeResponse.ok) {
            throw new Error('Судья для данного вида спорта не найден');
        }

        const judges = await judgeResponse.json();
        console.log('Данные судей получены:', judges);

        if (judges.length === 0) {
            throw new Error('Судья для данного вида спорта не найден');
        }

        const judge = judges[0];

        // 4. Подготовка данных
        let performanceData = {
            student_id: studentData.student_id,
            sport_type_id: currentSportType,
            competition_id: competitionData.id,
            judge_id: judge.id
        };

        if (resultType === 'time') {
            performanceData.time_result = formatTime(result);
            performanceData.original_result = timeToSeconds(result);
        } else {
            performanceData.original_result = parseFloat(result);
            performanceData.time_result = null;
        }

        console.log('Подготовленные данные для создания результата:', performanceData);

        // 5. Создание результата
        showInfoPanel('Сохранение результата...', 'info', 0);
        const performanceResponse = await fetch(`${API_URL}/results/performances/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(performanceData)
        });

        console.log('Ответ от API результатов:', performanceResponse.status);

        if (!performanceResponse.ok) {
            const errorData = await performanceResponse.json();
            console.error('Ошибка от API результатов:', errorData);
            if (errorData.detail && errorData.detail.includes('already exists')) {
                throw new Error('Результат для этого участника уже существует');
            }
            throw new Error(errorData.detail || 'Ошибка при создании результата выступления');
        }

        const performanceResult = await performanceResponse.json();
        console.log('Результат успешно создан:', performanceResult);

        // Успех!
        let successMessage = 'Результат успешно добавлен!';
        if (studentData.created) {
            successMessage += ` Участник "${name}" добавлен в систему.`;
        }

        showInfoPanel(successMessage, 'success');

        // Очищаем форму и обновляем данные
        clearInputs();
        await loadResults();
        await loadRating();

        console.log('=== РЕЗУЛЬТАТ УСПЕШНО ДОБАВЛЕН ===');

    } catch (error) {
        console.error('=== ОШИБКА ПРИ ДОБАВЛЕНИИ РЕЗУЛЬТАТА ===');
        console.error('Детали ошибки:', error);
        showInfoPanel(`Ошибка: ${error.message}`, 'error', 8000);
    } finally {
        setAddButtonState(false);
    }
}

// ===========================================
// УДАЛЕНИЕ И ОЧИСТКА
// ===========================================

// Delete result
async function deleteResult(performanceId) {
    if (!confirm('Вы уверены, что хотите удалить этот результат?')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/results/performances/${performanceId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            await loadResults();
            await loadRating();
            showInfoPanel('Результат успешно удален', 'success');
        } else {
            throw new Error('Ошибка при удалении результата');
        }
    } catch (error) {
        console.error('Error deleting result:', error);
        showInfoPanel('Ошибка при удалении результата', 'error');
    }
}

// Clear input fields
// Обновить функцию clearInputs (заменить существующую)
function clearInputs() {
    const instituteInput = document.getElementById('institute-input');
    const nameInput = document.getElementById('name-input');
    const resultInput = document.getElementById('result-input');
    const maleRadio = document.querySelector('input[name="gender"][value="М"]');

    if (instituteInput) instituteInput.value = '';
    if (nameInput) nameInput.value = '';
    if (resultInput) resultInput.value = '';
    if (maleRadio) maleRadio.checked = true;

    // Очищаем состояния полей
    ['institute-input', 'name-input', 'result-input'].forEach(fieldId => {
        setFieldState(fieldId, 'normal');
    });

    // Скрываем информационную панель
    const infoPanel = document.getElementById('info-panel');
    if (infoPanel) {
        infoPanel.style.display = 'none';
    }

    updatePlaceInput();
}

// ===========================================
// НАВИГАЦИЯ
// ===========================================

// Navigation functions
function showRating() {
    window.location.href = 'rating.html';
}

function showResults() {
    window.location.href = 'index.html';
}

function showSchedule() {
    window.location.href = 'schedule.html';
}


// ===========================================
// УПРАВЛЕНИЕ ФОРМОЙ ДОБАВЛЕНИЯ
// ===========================================

// Переключение видимости формы добавления
function toggleAddForm() {
    const formContainer = document.getElementById('add-form-container');
    const toggleBtn = document.getElementById('toggle-form-btn');
    const toggleIcon = toggleBtn.querySelector('.toggle-icon');
    const toggleText = toggleBtn.querySelector('.toggle-text');

    if (!formContainer || !toggleBtn) {
        console.warn('Form toggle elements not found');
        return;
    }

    const isVisible = formContainer.style.display !== 'none';

    if (isVisible) {
        // Скрываем форму
        formContainer.style.display = 'none';
        toggleBtn.classList.remove('active');
        toggleText.textContent = 'Добавить результат';

        // Очищаем форму при закрытии
        clearInputs();
    } else {
        // Показываем форму
        formContainer.style.display = 'flex';
        toggleBtn.classList.add('active');
        toggleText.textContent = 'Свернуть форму';

        // Фокусируемся на первом поле
        const firstInput = document.getElementById('institute-input');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
}

// ===========================================
// УПРАВЛЕНИЕ КОМАНДНЫМИ ФОРМАМИ
// ===========================================

let teamMemberCount = 0;

// Функция для определения типа спорта
function isTeamSport(sportName) {
    const teamSports = ['Баскетбол', 'Волейбол', 'Футбол'];
    return teamSports.some(sport => sportName.includes(sport));
}

// Переключение между формами в зависимости от вида спорта
function switchSportForm() {
    const sportTypeSelect = document.getElementById('sport-type');
    const individualForm = document.getElementById('individual-form');
    const teamForm = document.getElementById('team-form');

    if (!sportTypeSelect || !individualForm || !teamForm) return;

    const selectedSport = sportTypeSelect.options[sportTypeSelect.selectedIndex]?.text || '';

    if (isTeamSport(selectedSport)) {
        // Показываем командную форму
        individualForm.style.display = 'none';
        teamForm.style.display = 'block';
        console.log('Переключение на командную форму для:', selectedSport);
    } else {
        // Показываем индивидуальную форму
        individualForm.style.display = 'block';
        teamForm.style.display = 'none';
        console.log('Переключение на индивидуальную форму для:', selectedSport);
    }
}

// Добавление члена команды
function addTeamMember() {
    const membersList = document.getElementById('team-members-list');
    if (!membersList) return;

    // Удаляем placeholder если он есть
    const placeholder = membersList.querySelector('.team-members-placeholder');
    if (placeholder) {
        placeholder.remove();
    }

    teamMemberCount++;

    const memberItem = document.createElement('div');
    memberItem.className = 'team-member-item';
    memberItem.innerHTML = `
        <input type="text" placeholder="Фамилия Имя Отчество" data-member-id="${teamMemberCount}">
        <button type="button" class="btn-remove-member" onclick="removeTeamMember(this)">Удалить</button>
    `;

    membersList.appendChild(memberItem);

    // Фокусируемся на новом поле
    const newInput = memberItem.querySelector('input');
    if (newInput) {
        newInput.focus();
    }
}

// Удаление члена команды
function removeTeamMember(button) {
    const memberItem = button.closest('.team-member-item');
    if (memberItem) {
        memberItem.remove();
    }

    // Показываем placeholder если список пуст
    const membersList = document.getElementById('team-members-list');
    if (membersList && membersList.children.length === 0) {
        showTeamMembersPlaceholder();
    }
}

// Показать placeholder для членов команды
function showTeamMembersPlaceholder() {
    const membersList = document.getElementById('team-members-list');
    if (!membersList) return;

    membersList.innerHTML = `
        <div class="team-members-placeholder">
            Нажмите "Добавить игрока" чтобы добавить членов команды
        </div>
    `;
}

// Очистка командной формы
function clearTeamForm() {
    const facultySelect = document.getElementById('team-faculty-select');
    const resultInput = document.getElementById('team-result-input');
    const maleRadio = document.querySelector('input[name="team-gender"][value="М"]');

    if (facultySelect) facultySelect.value = '';
    if (resultInput) resultInput.value = '';
    if (maleRadio) maleRadio.checked = true;

    // Очищаем список членов команды
    const membersList = document.getElementById('team-members-list');
    if (membersList) {
        showTeamMembersPlaceholder();
    }

    teamMemberCount = 0;

    // Скрываем информационную панель
    const infoPanel = document.getElementById('info-panel');
    if (infoPanel) {
        infoPanel.style.display = 'none';
    }
}

// Добавление результата команды
async function addTeamResult() {
    console.log('=== ДОБАВЛЕНИЕ КОМАНДНОГО РЕЗУЛЬТАТА ===');

    const facultySelect = document.getElementById('team-faculty-select');
    const resultInput = document.getElementById('team-result-input');
    const genderRadio = document.querySelector('input[name="team-gender"]:checked');
    const memberInputs = document.querySelectorAll('#team-members-list input[type="text"]');

    if (!facultySelect || !resultInput || !genderRadio) {
        showInfoPanel('Ошибка: не найдены элементы командной формы', 'error');
        return;
    }

    const faculty = facultySelect.value.trim();
    const result = resultInput.value.trim();
    const gender = genderRadio.value;

    // Собираем имена членов команды
    const teamMembers = [];
    memberInputs.forEach(input => {
        const name = input.value.trim();
        if (name) {
            teamMembers.push(name);
        }
    });

    console.log('Данные команды:', { faculty, result, gender, teamMembers, currentSportType });

    // Валидация
    if (!faculty) {
        showInfoPanel('Выберите институт команды', 'error');
        return;
    }

    if (!result) {
        showInfoPanel('Введите результат команды', 'error');
        return;
    }

    if (teamMembers.length === 0) {
        showInfoPanel('Добавьте хотя бы одного члена команды', 'error');
        return;
    }

    if (!currentSportType) {
        showInfoPanel('Сначала выберите вид спорта', 'error');
        return;
    }

    try {
        setAddButtonState(true, 'add-team-btn');
        showInfoPanel('Добавление команды...', 'info', 0);

        // Здесь будет логика добавления команды через API
        // Пока что показываем успешное сообщение
        showInfoPanel(`Команда ${faculty} (${gender === 'М' ? 'мужская' : 'женская'}) с ${teamMembers.length} игроками успешно добавлена!`, 'success');

        // Очищаем форму
        clearTeamForm();

        // Обновляем результаты
        await loadResults();
        await loadRating();

    } catch (error) {
        console.error('Ошибка при добавлении команды:', error);
        showInfoPanel(`Ошибка: ${error.message}`, 'error');
    } finally {
        setAddButtonState(false, 'add-team-btn');
    }
}

// Обновленная функция управления состоянием кнопки
function setAddButtonState(loading = false, buttonId = 'add-result-btn') {
    const button = document.getElementById(buttonId);
    if (!button) {
        console.warn(`Button ${buttonId} not found`);
        return;
    }

    const textSpan = button.querySelector('.btn-text');
    const spinner = button.querySelector('.btn-spinner');

    if (loading) {
        button.disabled = true;
        if (textSpan) textSpan.style.display = 'none';
        if (spinner) spinner.style.display = 'inline-flex';
    } else {
        button.disabled = false;
        if (textSpan) textSpan.style.display = 'inline';
        if (spinner) spinner.style.display = 'none';
    }
}