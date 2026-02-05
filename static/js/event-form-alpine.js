(function() {
    'use strict';

    console.log('[EventForm] Component script loading...');

    const registerComponents = () => {
        console.log('[EventForm] Registering Alpine components...');

        if (typeof Alpine === 'undefined') {
            console.error('[EventForm] Alpine is not defined!');
            return;
        }

        Alpine.data('createEvent', () => ({
            step: 1,
            totalSteps: 4,
            eventType: 'IN_PERSON',
            coverPreview: null,
            organization: '',
            title: '',
            description: '',
            startAt: '',
            endAt: '',
            location: '',
            contactEmail: '',
            contactPhone: '',
            errors: {},

            async handleCoverUpload(e) {
                const file = e.target.files[0];
                if (file && window.ImageCompressor) {
                    const compressed = await ImageCompressor.processFileInput(e.target);
                    this.coverPreview = URL.createObjectURL(compressed);
                } else if (file) {
                    this.coverPreview = URL.createObjectURL(file);
                }
            },

            clearError(field) {
                delete this.errors[field];
            },

            validateStep1() {
                this.errors = {};
                if (!this.organization) this.errors.organization = 'Please select an organization';
                if (!this.title.trim()) this.errors.title = 'Event title is required';
                if (!this.description.trim()) this.errors.description = 'Description is required';
                return Object.keys(this.errors).length === 0;
            },

            validateStep2() {
                this.errors = {};
                if (!this.startAt) this.errors.startAt = 'Start date and time is required';
                if (!this.endAt) this.errors.endAt = 'End date and time is required';
                return Object.keys(this.errors).length === 0;
            },

            validateStep3() {
                this.errors = {};
                if (this.eventType !== 'ONLINE' && !this.location.trim()) {
                    this.errors.location = 'Address is required for in-person events';
                }
                return Object.keys(this.errors).length === 0;
            },

            validateStep4() {
                this.errors = {};
                if (!this.contactEmail && !this.contactPhone) {
                    this.errors.contact = 'Please provide at least one contact method';
                }
                return Object.keys(this.errors).length === 0;
            },

            nextStep() {
                let valid = false;
                if (this.step === 1) valid = this.validateStep1();
                else if (this.step === 2) valid = this.validateStep2();
                else if (this.step === 3) valid = this.validateStep3();
                else valid = true;
                if (valid && this.step < this.totalSteps) this.step++;
            },

            prevStep() {
                this.errors = {};
                if (this.step > 1) this.step--;
            },

            submitForm(e) {
                if (!this.validateStep4()) {
                    e.preventDefault();
                }
            },

            init() {
                this.$watch('step', (value) => {
                    if (value === 2) {
                        const tryInit = (attempts = 0) => {
                            if (attempts >= 5) return;
                            setTimeout(() => {
                                if (window.initDatePickers && !window.initDatePickers()) {
                                    tryInit(attempts + 1);
                                }
                            }, 100 + (attempts * 100));
                        };
                        tryInit();
                    }
                });
            }
        }));

        Alpine.data('editEvent', (eventData = {}) => ({
            step: 1,
            totalSteps: 4,
            eventType: eventData.eventType || 'IN_PERSON',
            coverPreview: eventData.coverPreview || null,
            title: eventData.title || '',
            description: eventData.description || '',
            startAt: eventData.startAt || '',
            endAt: eventData.endAt || '',
            location: eventData.location || '',
            contactEmail: eventData.contactEmail || '',
            contactPhone: eventData.contactPhone || '',
            errors: {},

            async handleCoverUpload(e) {
                const file = e.target.files[0];
                if (file && window.ImageCompressor) {
                    const compressed = await ImageCompressor.processFileInput(e.target);
                    this.coverPreview = URL.createObjectURL(compressed);
                } else if (file) {
                    this.coverPreview = URL.createObjectURL(file);
                }
            },

            clearError(field) {
                delete this.errors[field];
            },

            validateStep1() {
                this.errors = {};
                if (!this.title.trim()) this.errors.title = 'Event title is required';
                if (!this.description.trim()) this.errors.description = 'Description is required';
                return Object.keys(this.errors).length === 0;
            },

            validateStep2() {
                this.errors = {};
                if (!this.startAt) this.errors.startAt = 'Start date and time is required';
                if (!this.endAt) this.errors.endAt = 'End date and time is required';
                return Object.keys(this.errors).length === 0;
            },

            validateStep3() {
                this.errors = {};
                if (this.eventType !== 'ONLINE' && !this.location.trim()) {
                    this.errors.location = 'Address is required for in-person events';
                }
                return Object.keys(this.errors).length === 0;
            },

            validateStep4() {
                this.errors = {};
                if (!this.contactEmail && !this.contactPhone) {
                    this.errors.contact = 'Please provide at least one contact method';
                }
                return Object.keys(this.errors).length === 0;
            },

            nextStep() {
                let valid = false;
                if (this.step === 1) valid = this.validateStep1();
                else if (this.step === 2) valid = this.validateStep2();
                else if (this.step === 3) valid = this.validateStep3();
                else valid = true;
                if (valid && this.step < this.totalSteps) this.step++;
            },

            prevStep() {
                this.errors = {};
                if (this.step > 1) this.step--;
            },

            submitForm(e) {
                if (!this.validateStep4()) {
                    e.preventDefault();
                }
            },

            init() {
                this.$watch('step', (value) => {
                    if (value === 2) {
                        const tryInit = (attempts = 0) => {
                            if (attempts >= 5) return;
                            setTimeout(() => {
                                if (window.initDatePickers && !window.initDatePickers()) {
                                    tryInit(attempts + 1);
                                }
                            }, 100 + (attempts * 100));
                        };
                        tryInit();
                    }
                });
            }
        }));

        console.log('[EventForm] Components registered successfully');
    };

    if (typeof Alpine !== 'undefined' && Alpine.version) {
        console.log('[EventForm] Alpine already loaded, registering immediately');
        registerComponents();
    } else {
        console.log('[EventForm] Waiting for alpine:init event');
        document.addEventListener('alpine:init', () => {
            console.log('[EventForm] alpine:init event fired');
            registerComponents();
        });
    }
})();
