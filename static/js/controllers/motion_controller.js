import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static values = {
        from: { type: Object, default: { opacity: 0, y: 8 } },
        to: { type: Object, default: { opacity: 1, y: 0 } },
        duration: { type: Number, default: 0.25 },
        delay: { type: Number, default: 0 }
    }

    connect() {
        this.animate();
    }

    animate() {
        if (typeof motion === 'undefined') {
            return;
        }

        const fromArray = Object.entries(this.fromValue).reduce((acc, [key, val]) => {
            acc[key] = Array.isArray(val) ? val : [val];
            return acc;
        }, {});

        const toArray = Object.entries(this.toValue).reduce((acc, [key, val]) => {
            acc[key] = Array.isArray(val) ? val : [val];
            return acc;
        }, {});

        const animation = { ...fromArray };
        Object.keys(toArray).forEach(key => {
            animation[key] = [...(fromArray[key] || [toArray[key][0]]), ...toArray[key]];
        });

        motion.animate(
            this.element,
            animation,
            {
                duration: this.durationValue,
                delay: this.delayValue
            }
        );
    }
}
