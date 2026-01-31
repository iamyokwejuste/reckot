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
            this.allEvents = JSON.parse(document.getElementById('events-data').textContent);
            this.categories = JSON.parse(document.getElementById('categories-data').textContent);
            this.filteredEvents = this.allEvents;
        },

        getEventStatus(event) {
            const now = new Date();
            const startAt = new Date(event.start_at);
            const endAt = new Date(event.end_at);

            if (now >= startAt && now <= endAt) {
                return { status: 'live', label: 'Live Now', class: 'badge badge-danger animate-pulse' };
            }

            if (now > endAt) {
                return { status: 'passed', label: 'Ended', class: 'badge badge-default' };
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

            return { status: 'upcoming', label: timeLabel, class: 'badge badge-success' };
        },

        filterEvents() {
            let events = this.allEvents;

            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase();
                events = events.filter(e =>
                    e.title.toLowerCase().includes(query) ||
                    e.description.toLowerCase().includes(query)
                );
            }

            if (this.locationQuery) {
                const loc = this.locationQuery.toLowerCase();
                events = events.filter(e =>
                    e.location.toLowerCase().includes(loc) ||
                    e.city.toLowerCase().includes(loc)
                );
            }

            if (this.selectedCategory) {
                events = events.filter(e => e.category_slug === this.selectedCategory);
            }

            if (this.selectedDate !== 'all') {
                const now = new Date();
                now.setHours(0, 0, 0, 0);
                events = events.filter(e => {
                    const eventDate = new Date(e.start_at);
                    eventDate.setHours(0, 0, 0, 0);

                    if (this.selectedDate === 'today') {
                        return eventDate.getTime() === now.getTime();
                    } else if (this.selectedDate === 'week') {
                        const weekFromNow = new Date(now);
                        weekFromNow.setDate(now.getDate() + 7);
                        return eventDate >= now && eventDate <= weekFromNow;
                    } else if (this.selectedDate === 'month') {
                        const monthFromNow = new Date(now);
                        monthFromNow.setMonth(now.getMonth() + 1);
                        return eventDate >= now && eventDate <= monthFromNow;
                    }
                    return true;
                });
            }

            this.filteredEvents = events;
        }
    }));
});
