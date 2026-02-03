document.addEventListener('alpine:init', () => {
    Alpine.data('discover', () => ({
        searchQuery: '',
        locationQuery: '',
        selectedCategory: '',
        selectedDate: 'all',
        filteredEvents: [],
        allEvents: [],
        categories: [],

        init() {
            this.loadData();
            this.filterEvents();
            this.$nextTick(() => {
                if (window.lucide) {
                    lucide.createIcons();
                }
            });
        },

        loadData() {
            const eventsEl = document.getElementById('events-data');
            const categoriesEl = document.getElementById('categories-data');

            if (eventsEl && eventsEl.textContent) {
                try {
                    this.allEvents = JSON.parse(eventsEl.textContent);
                } catch (error) {
                    console.error('Failed to parse events data:', error);
                    this.allEvents = [];
                }
            }

            if (categoriesEl && categoriesEl.textContent) {
                try {
                    this.categories = JSON.parse(categoriesEl.textContent);
                } catch (error) {
                    console.error('Failed to parse categories data:', error);
                    this.categories = [];
                }
            }
        },

        getEventStatus(event) {
            const now = new Date();
            const startAt = new Date(event.start_at);
            const endAt = new Date(event.end_at);

            if (now >= startAt && now <= endAt) {
                return {
                    status: 'live',
                    label: 'Live Now',
                    class: 'badge badge-danger animate-pulse'
                };
            }

            if (now > endAt) {
                return {
                    status: 'passed',
                    label: 'Ended',
                    class: 'badge badge-default'
                };
            }

            const diff = startAt - now;
            const minutes = Math.floor(diff / 60000);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);
            const months = Math.floor(days / 30);

            let timeLabel;
            if (months > 0) {
                timeLabel = months === 1 ? 'in 1 month' : `in ${months} months`;
            } else if (days > 0) {
                timeLabel = days === 1 ? 'in 1 day' : `in ${days} days`;
            } else if (hours > 0) {
                timeLabel = hours === 1 ? 'in 1 hour' : `in ${hours} hours`;
            } else {
                timeLabel = minutes === 1 ? 'in 1 minute' : `in ${minutes} minutes`;
            }

            return {
                status: 'upcoming',
                label: timeLabel,
                class: 'badge badge-success'
            };
        },

        filterEvents() {
            let events = [...this.allEvents];

            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase();
                events = events.filter(e =>
                    e.title.toLowerCase().includes(query) ||
                    (e.description && e.description.toLowerCase().includes(query))
                );
            }

            if (this.locationQuery) {
                const loc = this.locationQuery.toLowerCase();
                events = events.filter(e =>
                    (e.location && e.location.toLowerCase().includes(loc)) ||
                    (e.city && e.city.toLowerCase().includes(loc))
                );
            }

            if (this.selectedCategory) {
                events = events.filter(e => e.category_slug === this.selectedCategory);
            }

            if (this.selectedDate !== 'all') {
                events = this.filterByDate(events, this.selectedDate);
            }

            this.filteredEvents = events;
        },

        filterByDate(events, dateFilter) {
            const now = new Date();
            now.setHours(0, 0, 0, 0);

            return events.filter(e => {
                const eventDate = new Date(e.start_at);
                eventDate.setHours(0, 0, 0, 0);

                switch (dateFilter) {
                    case 'today':
                        return eventDate.getTime() === now.getTime();

                    case 'week':
                        const dayOfWeek = now.getDay();
                        const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
                        const startOfWeek = new Date(now);
                        startOfWeek.setDate(now.getDate() - daysToMonday);
                        const endOfWeek = new Date(startOfWeek);
                        endOfWeek.setDate(startOfWeek.getDate() + 6);
                        endOfWeek.setHours(23, 59, 59, 999);
                        return eventDate >= startOfWeek && eventDate <= endOfWeek;

                    case 'month':
                        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
                        const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                        endOfMonth.setHours(23, 59, 59, 999);
                        return eventDate >= startOfMonth && eventDate <= endOfMonth;

                    default:
                        return true;
                }
            });
        }
    }));
});
