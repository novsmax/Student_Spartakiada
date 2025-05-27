const API_URL = 'http://localhost:8000/api';
let authToken = localStorage.getItem('authToken');
let userRole = localStorage.getItem('userRole');
let currentSportType = null;

document.addEventListener('DOMContentLoaded', async () => {
    await loadSportTypes();
    await loadResults();
    await loadRating();
    updateUIByRole();

    document.getElementById('sport-type').addEventListener('change', async (e) => {
        currentSportType = e.target.value ? parseInt(e.target.value) : null;
        await loadResults();
    });

    document.getElementById('login-form').addEventListener('submit', handleLogin);
});

async function loadSportTypes() {
    try {
        const response = await fetch(`${API_URL}/sport-types/`);
        const sportTypes = await response.json();

        const select = document.getElementById('sport-type');
        select.innerHTML = '<option value="">Все виды</option>';

        sportTypes.forEach(sport => {
            const option = document.createElement('option');
            option.value = sport.id;
            option.textContent = sport.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading sport types:', error);
    }
}

async function loadResults() {
    try {
        let url = `${API_URL}/results/competition-results/`;
        if (currentSportType) {
            url += `?sport_type_id=${currentSportType}`;
        }

        const response = await fetch(url);
        const results = await response.json();

        const tbody = document.getElementById('results-tbody');
        tbody.innerHTML = '';

        results.forEach(facultyResult => {
            facultyResult.performances.forEach((performance, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${facultyResult.place}</td>
                    <td>${facultyResult.faculty_abbreviation}</td>
                    <td>${performance.student_name}</td>
                    <td>${performance.time_result || '-'}</td>
                    <td>${performance.points}</td>
                    <td>
                        ${userRole === 'judge' || userRole === 'admin' ?
                            `<button class="btn-delete" onclick="deleteResult(${performance.id})">Удалить</button>` :
                            ''}
                    </td>
                `;
                tbody.appendChild(row);
            });
        });
    } catch (error) {
        console.error('Error loading results:', error);
    }
}

async function loadRating() {
    try {
        const response = await fetch(`${API_URL}/results/spartakiada-rating/`);
        const ratings = await response.json();

        const ratingList = document.getElementById('rating-list');
        ratingList.innerHTML = '';

        ratings.forEach(rating => {
            const item = document.createElement('div');
            item.className = 'rating-item';
            item.innerHTML = `
                <span>${rating.overall_place}. ${rating.faculty_abbreviation}</span>
                <span>${Math.round(rating.total_points)}</span>
            `;
            ratingList.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading rating:', error);
    }
}

async function addResult() {
    if (!authToken) {
        showLoginModal();
        return;
    }

    const place = document.getElementById('place-input').value;
    const institute = document.getElementById('institute-input').value;
    const name = document.getElementById('name-input').value;
    const result = document.getElementById('result-input').value;
    const gender = document.querySelector('input[name="gender"]:checked').value;

    if (!place || !institute || !name || !result) {
        alert('Пожалуйста, заполните все поля');
        return;
    }

    // This is a simplified version - in real app, you'd need to:
    // 1. Find or create student
    // 2. Find faculty by abbreviation
    // 3. Create performance record

    try {
        alert('Функция добавления результата будет реализована после настройки всех API endpoints');
        clearInputs();
        await loadResults();
        await loadRating();
    } catch (error) {
        console.error('Error adding result:', error);
        alert('Ошибка при добавлении результата');
    }
}

async function deleteResult(performanceId) {
    if (!authToken) {
        showLoginModal();
        return;
    }

    if (!confirm('Вы уверены, что хотите удалить этот результат?')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/results/performances/${performanceId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
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

function clearInputs() {
    document.getElementById('place-input').value = '';
    document.getElementById('institute-input').value = '';
    document.getElementById('name-input').value = '';
    document.getElementById('result-input').value = '';
    document.querySelector('input[name="gender"][value="М"]').checked = true;
}

async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            userRole = data.role;

            localStorage.setItem('authToken', authToken);
            localStorage.setItem('userRole', userRole);

            closeLoginModal();
            updateUIByRole();
        } else {
            alert('Неверный логин или пароль');
        }
    } catch (error) {
        console.error('Error during login:', error);
        alert('Ошибка при входе в систему');
    }
}

function updateUIByRole() {
    const deleteButtons = document.querySelectorAll('.btn-delete');
    const addButton = document.querySelector('.btn-add');

    if (userRole === 'judge' || userRole === 'admin') {
        deleteButtons.forEach(btn => btn.style.display = 'inline-block');
        if (addButton) addButton.style.display = 'inline-block';
    } else {
        deleteButtons.forEach(btn => btn.style.display = 'none');
        if (addButton) addButton.style.display = 'none';
    }
}

function showLoginModal() {
    document.getElementById('login-modal').style.display = 'block';
}

function closeLoginModal() {
    document.getElementById('login-modal').style.display = 'none';
    document.getElementById('login-form').reset();
}

function showRating() {
    alert('Переход на страницу рейтинга спартакиады');
}

function showResults() {
    location.reload();
}

function showSchedule() {
    alert('Переход на страницу расписания соревнований');
}

window.onclick = function(event) {
    const modal = document.getElementById('login-modal');
    if (event.target === modal) {
        closeLoginModal();
    }
};