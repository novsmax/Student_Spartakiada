const API_URL = 'http://localhost:8000/api';
let currentSportType = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await loadSportTypes();
        await loadResults();
        await loadRating();
    } catch (error) {
        console.error('Error initializing app:', error);
    }
    
    // Set up event listeners
    document.getElementById('sport-type').addEventListener('change', async (e) => {
        currentSportType = e.target.value ? parseInt(e.target.value) : null;
        await loadResults();
        await loadRating();
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
        select.innerHTML = '<option value="">Все виды</option>';
        
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

// Load competition results
async function loadResults() {
    try {
        let url = `${API_URL}/results/competition-results/`;
        if (currentSportType) {
            url += `?sport_type_id=${currentSportType}`;
        }
        
        console.log('Loading results from:', url);
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const results = await response.json();
        console.log('Results loaded:', results);
        
        const tbody = document.getElementById('results-tbody');
        tbody.innerHTML = '';
        
        if (Array.isArray(results)) {
            if (results.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Нет результатов</td></tr>';
                return;
            }
            
            // Определяем, командный ли это вид спорта
            const sportName = document.querySelector(`#sport-type option[value="${currentSportType}"]`)?.textContent || '';
            const isTeamSport = ['Баскетбол', 'Волейбол', 'Футбол'].some(sport => sportName.includes(sport));
            
            if (isTeamSport && currentSportType) {
                // Для командных видов спорта группируем по институтам
                const facultyGroups = {};
                results.forEach(performance => {
                    if (!facultyGroups[performance.faculty_id]) {
                        facultyGroups[performance.faculty_id] = {
                            faculty_abbreviation: performance.faculty_abbreviation,
                            place: performance.place,
                            points: performance.points,
                            members: []
                        };
                    }
                    facultyGroups[performance.faculty_id].members.push(performance.student_name);
                });
                
                // Отображаем командные результаты
                Object.values(facultyGroups).forEach(group => {
                    let placeClass = '';
                    if (group.place === 1) placeClass = 'gold-place';
                    else if (group.place === 2) placeClass = 'silver-place';
                    else if (group.place === 3) placeClass = 'bronze-place';
                    
                    // Заголовок команды
                    const headerRow = document.createElement('tr');
                    headerRow.style.backgroundColor = '#f0f0f0';
                    headerRow.style.fontWeight = 'bold';
                    headerRow.innerHTML = `
                        <td class="${placeClass}">${group.place}</td>
                        <td colspan="2">${group.faculty_abbreviation} - Команда</td>
                        <td>-</td>
                        <td>${group.points.toFixed(2)}</td>
                        <td></td>
                    `;
                    tbody.appendChild(headerRow);
                    
                    // Члены команды
                    group.members.forEach(member => {
                        const memberRow = document.createElement('tr');
                        memberRow.style.fontStyle = 'italic';
                        memberRow.innerHTML = `
                            <td></td>
                            <td></td>
                            <td style="padding-left: 30px;">↳ ${member}</td>
                            <td>-</td>
                            <td>${group.points.toFixed(2)}</td>
                            <td></td>
                        `;
                        tbody.appendChild(memberRow);
                    });
                });
            } else {
                // Для индивидуальных видов спорта
                results.forEach(performance => {
                    const row = document.createElement('tr');
                    
                    let placeClass = '';
                    if (performance.place === 1) placeClass = 'gold-place';
                    else if (performance.place === 2) placeClass = 'silver-place';
                    else if (performance.place === 3) placeClass = 'bronze-place';
                    
                    let resultDisplay = performance.time_result || '-';
                    if (performance.time_result) {
                        resultDisplay = performance.time_result;
                    } else if (!currentSportType || currentSportType > 3) {
                        resultDisplay = `${performance.points.toFixed(2)} балла`;
                    }
                    
                    row.innerHTML = `
                        <td class="${placeClass}" style="font-weight: bold;">${performance.place}</td>
                        <td>${performance.faculty_abbreviation}</td>
                        <td>${performance.student_name}</td>
                        <td>${resultDisplay}</td>
                        <td>${performance.points.toFixed(2)}</td>
                        <td>
                            <button class="btn-delete" onclick="deleteResult(${performance.performance_id})">Удалить</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
        } else {
            console.error('Results is not an array:', results);
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Ошибка загрузки данных</td></tr>';
        }
    } catch (error) {
        console.error('Error loading results:', error);
        const tbody = document.getElementById('results-tbody');
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Ошибка загрузки результатов</td></tr>';
    }
}

// Load rating
async function loadRating() {
    try {
        let url = `${API_URL}/results/faculty-sport-rating/`;
        if (currentSportType) {
            url += `?sport_type_id=${currentSportType}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) {
            const fallbackResponse = await fetch(`${API_URL}/results/spartakiada-rating/`);
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
        
        // Обновляем заголовок рейтинга
        const ratingTitle = document.querySelector('.rating-panel h3');
        if (ratingTitle) {
            if (currentSportType) {
                const sportName = document.querySelector(`#sport-type option[value="${currentSportType}"]`)?.textContent || '';
                ratingTitle.textContent = `Баллы: ${sportName}`;
            } else {
                ratingTitle.textContent = 'Баллы: Общий зачет';
            }
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