// Course Generator UI Application
class CourseGeneratorApp {
    constructor() {
        this.apiBase = 'http://localhost:3002/api';
        this.currentUser = null;
        this.currentStep = 1;
        this.courseData = {};
        this.init();
    }

    init() {
        this.checkAuthStatus();
        this.setupEventListeners();
    }

    // Authentication Methods
    async checkAuthStatus() {
        try {
            const response = await axios.get(`${this.apiBase}/auth/me`, {
                withCredentials: true
            });
            this.setUser(response.data.user);
        } catch (error) {
            console.log('Not authenticated');
        }
    }

    setUser(user) {
        this.currentUser = user;
        document.getElementById('userName').textContent = user.name;
        document.getElementById('navAuth').style.display = 'none';
        document.getElementById('navUser').style.display = 'flex';
    }

    clearUser() {
        this.currentUser = null;
        document.getElementById('navAuth').style.display = 'flex';
        document.getElementById('navUser').style.display = 'none';
    }

    async handleLogin(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        
        try {
            const response = await axios.post(`${this.apiBase}/auth/login`, {
                email: formData.get('email'),
                password: formData.get('password')
            }, {
                withCredentials: true
            });

            this.setUser(response.data.user);
            this.closeModal('loginModal');
            this.showToast('ログインに成功しました', 'success');
            event.target.reset();
        } catch (error) {
            this.showToast(error.response?.data?.error || 'ログインに失敗しました', 'error');
        }
    }

    async handleRegister(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');
        
        if (password !== confirmPassword) {
            this.showToast('パスワードが一致しません', 'error');
            return;
        }

        try {
            const response = await axios.post(`${this.apiBase}/auth/register`, {
                name: formData.get('name'),
                email: formData.get('email'),
                password: password
            }, {
                withCredentials: true
            });

            this.setUser(response.data.user);
            this.closeModal('registerModal');
            this.showToast('登録に成功しました', 'success');
            event.target.reset();
        } catch (error) {
            this.showToast(error.response?.data?.error || '登録に失敗しました', 'error');
        }
    }

    async logout() {
        try {
            await axios.post(`${this.apiBase}/auth/logout`, {}, {
                withCredentials: true
            });
            this.clearUser();
            this.showToast('ログアウトしました', 'success');
        } catch (error) {
            this.showToast('ログアウトに失敗しました', 'error');
        }
    }

    // Modal Methods
    showModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }

    showLogin() {
        this.showModal('loginModal');
    }

    showRegister() {
        this.showModal('registerModal');
    }

    // Course Generator Methods
    showCourseGenerator() {
        this.resetWizard();
        this.showModal('courseGeneratorModal');
    }

    resetWizard() {
        this.currentStep = 1;
        this.courseData = {};
        this.showStep(1);
        document.getElementById('progressLog').innerHTML = '';
        document.getElementById('resultsContainer').innerHTML = '';
    }

    showStep(step) {
        // Hide all steps
        document.querySelectorAll('.wizard-step').forEach(el => {
            el.classList.remove('active');
        });
        
        // Show current step
        document.getElementById(`step${step}`).classList.add('active');
        this.currentStep = step;
    }

    nextStep(step) {
        if (this.validateCurrentStep()) {
            this.showStep(step);
        }
    }

    prevStep(step) {
        this.showStep(step);
    }

    validateCurrentStep() {
        switch (this.currentStep) {
            case 1:
                const sourceType = document.querySelector('.source-option.selected');
                if (!sourceType) {
                    this.showToast('ソースタイプを選択してください', 'warning');
                    return false;
                }
                
                if (sourceType.dataset.type === 'url') {
                    const urls = document.getElementById('sourceUrls').value.trim();
                    if (!urls) {
                        this.showToast('URLを入力してください', 'warning');
                        return false;
                    }
                } else if (sourceType.dataset.type === 'text') {
                    const text = document.getElementById('sourceText').value.trim();
                    if (!text) {
                        this.showToast('テキストを入力してください', 'warning');
                        return false;
                    }
                }
                break;
                
            case 2:
                const title = document.getElementById('courseTitle').value.trim();
                const description = document.getElementById('courseDescription').value.trim();
                
                if (!title || !description) {
                    this.showToast('コースタイトルと説明を入力してください', 'warning');
                    return false;
                }
                break;
        }
        return true;
    }

    selectSourceType(type) {
        // Remove selected class from all options
        document.querySelectorAll('.source-option').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Add selected class to clicked option
        event.target.closest('.source-option').classList.add('selected');
        event.target.closest('.source-option').dataset.type = type;
        
        // Show/hide input fields
        document.getElementById('urlInput').style.display = type === 'url' ? 'block' : 'none';
        document.getElementById('textInput').style.display = type === 'text' ? 'block' : 'none';
    }

    async generateCourse() {
        this.showStep(4);
        
        // Prepare course data
        const sourceType = document.querySelector('.source-option.selected').dataset.type;
        const sources = [];
        
        if (sourceType === 'url') {
            const urls = document.getElementById('sourceUrls').value.trim().split('\n');
            urls.forEach(url => {
                if (url.trim()) {
                    sources.push({
                        type: 'url',
                        content: url.trim()
                    });
                }
            });
        } else if (sourceType === 'text') {
            sources.push({
                type: 'text',
                content: document.getElementById('sourceText').value.trim()
            });
        }

        const courseData = {
            sources: sources,
            metadata: {
                course_title: document.getElementById('courseTitle').value,
                course_description: document.getElementById('courseDescription').value,
                specialty_field: document.getElementById('specialtyField').value,
                profession: document.getElementById('profession').value,
                avatar: document.getElementById('avatar').value,
                tone_of_voice: document.getElementById('toneOfVoice').value
            },
            options: {
                includeAudio: document.getElementById('includeAudio').checked,
                language: document.getElementById('language').value,
                audioVoice: document.getElementById('audioVoice').value
            }
        };

        try {
            this.updateProgress('コース生成を開始しています...');
            
            const response = await axios.post(`${this.apiBase}/generate-course`, courseData, {
                withCredentials: true,
                timeout: 300000 // 5 minutes timeout
            });

            this.courseData = response.data;
            this.updateProgress('コース生成が完了しました！');
            this.displayResults(response.data);
            this.showStep(5);
            
        } catch (error) {
            console.error('Course generation error:', error);
            this.updateProgress('エラー: ' + (error.response?.data?.error || 'コース生成に失敗しました'));
            this.showToast('コース生成に失敗しました', 'error');
        }
    }

    updateProgress(message) {
        const progressText = document.getElementById('progressText');
        const progressLog = document.getElementById('progressLog');
        
        progressText.textContent = message;
        
        const timestamp = new Date().toLocaleTimeString();
        progressLog.innerHTML += `<div>[${timestamp}] ${message}</div>`;
        progressLog.scrollTop = progressLog.scrollHeight;
    }

    displayResults(data) {
        const container = document.getElementById('resultsContainer');
        
        if (data.course) {
            const course = data.course;
            container.innerHTML = `
                <div class="course-preview">
                    <h3 class="course-title">${course.title || 'Untitled Course'}</h3>
                    <p class="course-description">${course.description || 'No description'}</p>
                    
                    <h4>レッスン一覧:</h4>
                    <ul class="lessons-list">
                        ${course.lessons ? course.lessons.map(lesson => `
                            <li class="lesson-item">
                                <strong>${lesson.title}</strong>
                                <p>${lesson.description || 'No description'}</p>
                                ${lesson.duration ? `<small>推定時間: ${lesson.duration}</small>` : ''}
                            </li>
                        `).join('') : '<li>レッスンが見つかりません</li>'}
                    </ul>
                </div>
            `;
        } else {
            container.innerHTML = '<p>生成されたコースデータが見つかりません。</p>';
        }
    }

    async exportCourse() {
        if (!this.courseData) {
            this.showToast('エクスポートするコースがありません', 'warning');
            return;
        }

        try {
            const response = await axios.post(`${this.apiBase}/export-course`, {
                course: this.courseData.course,
                scripts: this.courseData.scripts || {},
                audioFiles: this.courseData.audioFiles || {},
                exportOptions: {
                    format: 'zip',
                    includeAudio: true,
                    includeScripts: true,
                    includeMetadata: true
                }
            }, {
                withCredentials: true,
                responseType: 'blob'
            });

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `course-${Date.now()}.zip`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);

            this.showToast('コースのエクスポートが完了しました', 'success');
        } catch (error) {
            this.showToast('エクスポートに失敗しました', 'error');
        }
    }

    // Utility Methods
    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        document.getElementById('toastContainer').appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    scrollToFeatures() {
        document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
    }

    setupEventListeners() {
        // Global click handler for modal backdrop
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.classList.remove('active');
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal.active').forEach(modal => {
                    modal.classList.remove('active');
                });
            }
        });
    }
}

// Initialize the application
const app = new CourseGeneratorApp();

// Global functions for HTML onclick handlers
function showLogin() {
    app.showLogin();
}

function showRegister() {
    app.showRegister();
}

function showCourseGenerator() {
    app.showCourseGenerator();
}

function closeModal(modalId) {
    app.closeModal(modalId);
}

function handleLogin(event) {
    app.handleLogin(event);
}

function handleRegister(event) {
    app.handleRegister(event);
}

function logout() {
    app.logout();
}

function selectSourceType(type) {
    app.selectSourceType(type);
}

function nextStep(step) {
    app.nextStep(step);
}

function prevStep(step) {
    app.prevStep(step);
}

function generateCourse() {
    app.generateCourse();
}

function resetWizard() {
    app.resetWizard();
}

function exportCourse() {
    app.exportCourse();
}

function scrollToFeatures() {
    app.scrollToFeatures();
}