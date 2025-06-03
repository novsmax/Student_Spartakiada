const API_URL = 'http://localhost:8000/api';
let currentSportType = null;
let currentGenderFilter = '';

// Обработка кликов по кнопкам выбора пола
function initGenderButtons() {
    const genderLabels = document.querySelectorAll('.gender-filter label');
    const genderRadios = document.querySelectorAll('input[name="filter-gender"]');

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
    try {
        await loadSportTypes();
        await loadResults();
        await loadRating();

        // Инициализация кнопок выбора пола
        initGenderButtons();
    } catch (error) {
        console.error('Error initializing app:', error);
    }

    // Set up event listeners
    document.getElementById('sport-type').addEventListener('change', async (e) => {
        currentSportType = e.target.value ? parseInt(e.target.value) : null;
        await loadResults();
        await loadRating();
        updatePlaceInput();
    });

    // Gender filter event listeners
    document.querySelectorAll('input[name="filter-gender"]').forEach(radio => {
        radio.addEventListener('change', async (e) => {
            currentGenderFilter = e.target.value;
            await loadResults();
            await loadRating();
        });
    });
});

// Load sport types for dropdown
async function loadSportTypes() {
    try {
        const response = await fetch(`${API_URL}/competitions/sport-types/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const sportTypes = await response.json();
        console.log('Sport types loaded:', sportTypes);

        const select = document.getElementById('sport-type');
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
        select.innerHTML = '<option value="">Ошибка загрузки</option>';
    }
}

// Update place input based on current results
function updatePlaceInput() {
    const tbody = document.getElementById('results-tbody');
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

        console.log('Loading results from:', url);

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const results = await response.json();
        console.log('Results loaded:', results);

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
        tbody.innerHTML = '<tr><td colspan="6" class="error-message">Ошибка загрузки результатов</td></tr>';
        updatePlaceInput();
    }
}

function displayTeamResultsWithPoints(results) {
    const tbody = document.getElementById('results-tbody');

    // Группируем по факультетам (в рамках одного пола)
    const facultyGroups = {};
    results.forEach(performance => {
        const facultyId = performance.faculty_id;
        if (!facultyGroups[facultyId]) {
            facultyGroups[facultyId] = {
                faculty_abbreviation: performance.faculty_abbreviation,
                place: performance.place,
                points: performance.points,
                members: []
            };
        }
        facultyGroups[facultyId].members.push(performance.student_name);
    });

    // ДОБАВЛЕНО: Сортируем команды по баллам (больше баллов = лучше место)
    const sortedGroups = Object.values(facultyGroups).sort((a, b) => b.points - a.points);

    // ДОБАВЛЕНО: Пересчитываем места после сортировки
    let currentPlace = 1;
    for (let i = 0; i < sortedGroups.length; i++) {
        if (i > 0 && sortedGroups[i].points !== sortedGroups[i - 1].points) {
            currentPlace = i + 1;
        }
        sortedGroups[i].place = currentPlace;
    }

    // Отображаем командные результаты с баллами в правильном порядке
    sortedGroups.forEach(group => {
        let placeClass = '';
        if (group.place === 1) placeClass = 'gold-place';
        else if (group.place === 2) placeClass = 'silver-place';
        else if (group.place === 3) placeClass = 'bronze-place';

        // Заголовок команды
        const headerRow = document.createElement('tr');
        headerRow.className = 'team-header';
        headerRow.innerHTML = `
            <td class="${placeClass}">${group.place}</td>
            <td colspan="2">${group.faculty_abbreviation} - Команда</td>
            <td>-</td>
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
}

function displayIndividualResultsWithPoints(results) {
    const tbody = document.getElementById('results-tbody');

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

    // ИСПРАВЛЕНО: данные уже приходят отсортированными с сервера,
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
                points: performance.points, // ИЗМЕНЕНО: получаем баллы из сервера
                members: []
            };
            // Сохраняем порядок первого появления команды
            teamOrder.push(teamKey);
        }
        teamGroups[teamKey].members.push(performance.student_name);
    });

    // ИСПРАВЛЕНО: отображаем команды в том порядке, в котором они пришли с сервера
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

        console.log('Loading rating from:', url);

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
        console.log('Ratings loaded:', ratings);
        displayRating(ratings);

    } catch (error) {
        console.error('Error loading rating:', error);
        const ratingList = document.getElementById('rating-list');
        ratingList.innerHTML = '<div style="text-align: center;">Ошибка загрузки рейтинга</div>';
    }
}

// Display rating
function displayRating(ratings) {
    const ratingList = document.getElementById('rating-list');
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

// Add new result
async function addResult() {
    const institute = document.getElementById('institute-input').value;
    const name = document.getElementById('name-input').value;
    const result = document.getElementById('result-input').value;
    const gender = document.querySelector('input[name="gender"]:checked').value;

    if (!institute || !name || !result) {
        alert('Пожалуйста, заполните все поля');
        return;
    }

    if (!currentSportType) {
        alert('Пожалуйста, выберите вид соревнований');
        return;
    }

    try {
        // TODO: Implement actual API call to add result
        alert('Функция добавления результата требует реализации API endpoint');
        clearInputs();
        await loadResults();
        await loadRating();
    } catch (error) {
        console.error('Error adding result:', error);
        alert('Ошибка при добавлении результата');
    }
}

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
        } else {
            alert('Ошибка при удалении результата');
        }
    } catch (error) {
        console.error('Error deleting result:', error);
        alert('Ошибка при удалении результата');
    }
}

// Clear input fields
function clearInputs() {
    document.getElementById('institute-input').value = '';
    document.getElementById('name-input').value = '';
    document.getElementById('result-input').value = '';
    document.querySelector('input[name="gender"][value="М"]').checked = true;
    updatePlaceInput();
}

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