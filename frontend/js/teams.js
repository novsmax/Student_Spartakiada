const API_URL = 'http://127.0.0.1:8000/api';
let currentSportType = null;
let currentFaculty = null;
let currentGenderFilter = '';

let teamsID = [];
let changes = [];

function showResults() {
    window.location.href = 'index.html';
}

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Инициализация приложения...');
    try {
        await loadSportTypes();
        await loadFaculties();
        await loadTeam();
        await loadStudents();

        initGenderButtons();

        console.log('Приложение успешно инициализировано');

    } catch (error) {
        console.error('Error initializing app:', error);
        showInfoPanel('Ошибка инициализации приложения', 'error');
    }

    const sportTypeSelect = document.getElementById('sport-type');
    if (sportTypeSelect) {
        sportTypeSelect.addEventListener('change', async (e) => {
            currentSportType = e.target.value ? parseInt(e.target.value) : null;
            console.log('Выбран вид спорта:', currentSportType);
            await loadStudents();
            await loadTeam();
            changes = [];
        });
    }

    const facultySelect = document.getElementById('faculty-type');
    if (facultySelect) {
        facultySelect.addEventListener('change', async (e) => {
            currentFaculty = e.target.value ? parseInt(e.target.value) : null;
            console.log('Выбран факультет:', currentFaculty);
            await loadStudents();
            await loadTeam();
            changes = [];
        });
    }
});

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

async function loadFaculties() {
    try {
        console.log('Загрузка факультетов...');
        const response = await fetch(`${API_URL}/competitions/faculties/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const faculties = await response.json();
        console.log('Факультеты загружены:', faculties);

        const select = document.getElementById('faculty-type');
        if (!select) {
            throw new Error('Institute input element not found');
        }

        select.innerHTML = '<option value="">Факультет</option>';

        if (Array.isArray(faculties)) {
            faculties.forEach(faculty => {
                const option = document.createElement('option');
                option.value = faculty.id;
                option.textContent = faculty.abbreviation;
                select.appendChild(option);
            });
        } else {
            console.error('Faculties is not an array:', faculties);
        }
    } catch (error) {
        console.error('Error loading faculties:', error);
        const select = document.getElementById('faculty-type');
        if (select) {
            select.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    }
}

async function loadTeam() {
    try {

        teamsID = [];

        const tbody = document.getElementById('teams-table');
        if (!currentFaculty) {
                tbody.innerHTML = '<tr><td colspan="6" class="no-sport-message">Выберите факультет</td></tr>';
                return;
        }

        if (!currentSportType) {
                tbody.innerHTML = '<tr><td colspan="6" class="no-sport-message">Выберите вид спорта</td></tr>';
                return;
        }

        let url = `${API_URL}/students/team_by_sport_faculty/?faculty_id=${currentFaculty}&sport_type_id=${currentSportType}`;

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const results = await response.json();
        console.log('Результаты загружены:', results);

        results.forEach(team => {
            teamsID.push([team.id, team.team_id, team.gender]);
        });

        tbody.innerHTML = '';
        results.forEach(team => {
            const row = document.createElement('tr');
            row.setAttribute('id', `team-${team.id}`);
            row.innerHTML = `
                <td>${team.first_name} ${team.last_name} ${team.middle_name}</td>
                <td style="text-align: center;">${team.group_number}</td>
                <td style="text-align: center;">${team.gender}</td>
                <td style="text-align: center;"><button class="btn-delete-team" onclick="outTeam(event)" id="del-${team.id}">Удалить</button></td>
            `;
            tbody.appendChild(row);
        });

        await correctingStudents(results);
        applyGenderFilter();

    } catch (error) {
        console.error('Error loading team:', error);
        const tbody = document.getElementById('teams-table');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="error-message">Ошибка загрузки команды</td></tr>';
        }
        return;
    }
}

async function loadStudents() {
    try{
        const tbody = document.getElementById('students-table');

        if (!currentFaculty) {
                tbody.innerHTML = '<tr><td colspan="6" class="no-sport-message">Выберите факультет</td></tr>';
                return;
        }

        let url = `${API_URL}/students/student_by_faculty/?faculty_id=${currentFaculty}`;

        if (currentGenderFilter) {
            url += `&gender=${currentGenderFilter}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const results = await response.json();
        console.log('Результаты загружены:', results);

        tbody.innerHTML = '';
        results.forEach(student => {
            const row = document.createElement('tr');
            row.setAttribute('id', `student-${student.id}`);
            row.innerHTML = `
                <td>${student.first_name} ${student.last_name} ${student.middle_name}</td>
                <td style="text-align: center;">${student.group_name}</td>
                <td style="text-align: center;">${student.gender}</td>
                <td style="text-align: center;"><button class="btn-add-team" onclick="toTeam(event)" id="add-${student.id}">Добавить</button></td>
            `;
            tbody.appendChild(row);
        });

        applyGenderFilter();

    } catch (error) {
        console.error('Error loading students:', error);
        const tbody = document.getElementById('students-table');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="error-message">Ошибка загрузки студентов</td></tr>';
        }
        return;
    }
}

async function correctingStudents(deletedMember){
    try{
        const tbody = document.getElementById(`students-table`);
        let deletedIds = null;

        if (!currentSportType) {
                return;
        }

        if(deletedMember.length >= 1){
            deletedIds = deletedMember.map(member => member.id);
        }else{
            deletedIds = deletedMember; 
        }

        deletedIds.forEach(id => {
            const row = document.getElementById(`student-${id}`);
            if (row) {
                row.remove();
            }
        });

    } catch (error) {
        console.error('Error loading students:', error);
        const tbody = document.getElementById(`students-table`);
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="error-message">Ошибка загрузки студентов</td></tr>';
        }
        return;
    }
}

function applyGenderFilter() {
    // Фильтруем таблицу студентов
    const studentRows = document.querySelectorAll('#students-table tr');
    studentRows.forEach(row => {
        if (row.cells && row.cells.length >= 3) {
            const gender = row.cells[2].textContent.trim();
            const shouldShow = !currentGenderFilter || gender === currentGenderFilter;
            row.style.display = shouldShow ? '' : 'none';
        }
    });
    
    // Фильтруем таблицу команды
    const teamRows = document.querySelectorAll('#teams-table tr');
    teamRows.forEach(row => {
        if (row.cells && row.cells.length >= 3) {
            const gender = row.cells[2].textContent.trim();
            const shouldShow = !currentGenderFilter || gender === currentGenderFilter;
            row.style.display = shouldShow ? '' : 'none';
        }
    });
}
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
            label.classList.remove('active', 'gender-all', 'gender-male', 'gender-female');
        });

        const checkedRadio = document.querySelector('input[name="filter-gender"]:checked');
        if (checkedRadio) {
            const label = checkedRadio.closest('label');
            label.classList.add('active');
            
            // Добавляем специфичные классы для стилизации
            const value = checkedRadio.value;
            if (value === '') {
                label.classList.add('gender-all');
            } else if (value === 'М') {
                label.classList.add('gender-male');
            } else if (value === 'Ж') {
                label.classList.add('gender-female');
            }
        }
    }

    // Обработчик для изменения фильтра пола
    async function handleGenderChange() {
        const checkedRadio = document.querySelector('input[name="filter-gender"]:checked');
        currentGenderFilter = checkedRadio ? checkedRadio.value : '';
        console.log('Изменен фильтр пола:', currentGenderFilter);
        
        updateActiveClasses();
        
        applyGenderFilter();
    }

    // Обработчик для радио-кнопок
    genderRadios.forEach(radio => {
        radio.addEventListener('change', handleGenderChange);
    });

    // Обработчик для кликов по лейблам
    genderLabels.forEach(label => {
        label.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if (radio && !radio.checked) {
                radio.checked = true;
                handleGenderChange();
            }
        });
    });
    // Инициализация начального состояния
    updateActiveClasses();
}

function toTeam(event){
    try{
        if (!currentSportType) {
                alert('Выберите вид спорта');
                return;
        }

        const tbody = document.getElementById('teams-table');
        const studentId = event.target.id.split('-')[1];
        const studentRow = document.getElementById(`student-${studentId}`);

        changes = changes.filter(change => change.studentId !== studentId);

        changes.push({
            action: 'add',
            studentId: studentId,
            sportType: currentSportType,
            faculty: currentFaculty,
            studentData: {
                name: studentRow.cells[0].textContent,
                group: studentRow.cells[1].textContent,
                gender: studentRow.cells[2].textContent
            }
        });

        const teamRow = document.createElement('tr');
        teamRow.setAttribute('id', `team-${studentId}`);
        teamRow.setAttribute('class', `new-tr`);
        teamRow.innerHTML = `
            <td>${studentRow.cells[0].textContent}</td>
            <td style="text-align: center;">${studentRow.cells[1].textContent}</td>
            <td style="text-align: center;">${studentRow.cells[2].textContent}</td>
            <td style="text-align: center;"><button class="btn-delete-team" onclick="outTeam(event)" id="del-${studentId}">Удалить</button></td>
        `;
        tbody.appendChild(teamRow);

        studentRow.remove();

        applyGenderFilter();

    } catch (error) {
        console.error('Error loading students:', error);
        const tbody = document.getElementById('students-table');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="error-message">Ошибка загрузки студентов</td></tr>';
        }
        return;
    }
}

function outTeam(event){
    try{
        if (!currentSportType) {
                alert('Выберите вид спорта');
                return;
        }

        const tbody = document.getElementById('students-table');
        const studentId = event.target.id.split('-')[1];
        const studentRow = document.getElementById(`team-${studentId}`);

        changes = changes.filter(change => change.studentId !== studentId);

        changes.push({
            action: 'remove',
            studentId: studentId,
            sportType: currentSportType,
            faculty: currentFaculty,
            studentData: {
                name: studentRow.cells[0].textContent,
                group: studentRow.cells[1].textContent,
                gender: studentRow.cells[2].textContent
            }
        });

        const teamRow = document.createElement('tr');
        teamRow.setAttribute('id', `student-${studentId}`);
        teamRow.setAttribute('class', `new-tr`);
        teamRow.innerHTML = `
            <td>${studentRow.cells[0].textContent}</td>
            <td style="text-align: center;">${studentRow.cells[1].textContent}</td>
            <td style="text-align: center;">${studentRow.cells[2].textContent}</td>
            <td style="text-align: center;"><button class="btn-add-team" onclick="toTeam(event)" id="add-${studentId}">Добавить</button></td>
        `;
        tbody.appendChild(teamRow);
        
        studentRow.remove();

        applyGenderFilter();

    } catch (error) {
        console.error('Error loading students:', error);
        const tbody = document.getElementById('students-table');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="error-message">Ошибка загрузки студентов</td></tr>';
        }
        return;
    }
}

async function deleteChanges(){
    try{
        if (changes.length === 0) {
            alert('Нет изменений для отмены');
            return;
        }

        changes = [];
        currentGenderFilter = '';

        await loadStudents();
        await loadTeam();

    } catch (error) {
        console.error('Error deleting changes:', error);
        alert('Ошибка при удалении изменений');
        return;
    }
}

async function saveCnages(){
    if (changes.length === 0) {
        alert('Нет изменений для сохранения');
        return;
    };
    
    currentGenderFilter = '';

    for (const change of changes) {
        let flag = true;
        for (const row of teamsID) {
            studentId = row[0];

            if(change){
                if(change.action === 'add' && change.studentId == studentId){
                    console.log(`уже в команде ${studentId}`);
                    flag = false;
                }
            }
        };
        let teamId = teamsID.find(row => row[2] == change.studentData.gender) || false;
        if(flag){
            if(change.action === 'add' && teamId){
                let url = `${API_URL}/students/new_student_team`;

                const response =  await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        student_id: parseInt(change.studentId),
                        team_id: parseInt(teamId[1])
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const results = await response.json();

                console.log(`${results.message} ${results.team_id} (${results.student_id})`);
            }else if(change.action === 'add' && !teamId){
                let urlTeam = `${API_URL}/students/create_new_team`;

                const responseTeam =  await fetch(urlTeam, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        sport_type_id: parseInt(currentSportType),
                        faculty_id: parseInt(currentFaculty)
                    })
                });

                if (!responseTeam.ok) {
                    throw new Error(`HTTP error! status: ${responseTeam.status}`);
                }

                const resultsTeam = await responseTeam.json();

                console.log(`${resultsTeam.message} - ${resultsTeam.team_id}`);

                let url = `${API_URL}/students/new_student_team`;

                const response =  await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        student_id: parseInt(change.studentId),
                        team_id: parseInt(resultsTeam.team_id)
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const results = await response.json();

                console.log(`${results.message} ${results.team_id} (${results.student_id})`);
            }else if(change.action === 'remove'){
                let url = `${API_URL}/students/delete_student_from_team`;

                const response =  await fetch(url, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        student_id: parseInt(change.studentId),
                        team_id: parseInt(teamId[1])
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const results = await response.json();

                console.log(`${results.message} ${results.team_id} (${results.student_id})`);
            }
        }
    }
    changes = [];
    await loadStudents();
    await loadTeam();
}