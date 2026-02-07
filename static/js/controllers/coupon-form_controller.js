import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["assignmentType", "individualEmail", "groupEmails", "eventWarning"]

    connect() {
        this.updateAssignment();
    }

    updateAssignment() {
        const assignmentInput = document.getElementById('assignment_type');
        const assignmentType = assignmentInput ? assignmentInput.value : 'PUBLIC';

        if (this.hasIndividualEmailTarget) {
            this.individualEmailTarget.classList.add('hidden');
        }
        if (this.hasGroupEmailsTarget) {
            this.groupEmailsTarget.classList.add('hidden');
        }

        if (assignmentType === 'INDIVIDUAL' && this.hasIndividualEmailTarget) {
            this.individualEmailTarget.classList.remove('hidden');
        } else if (assignmentType === 'GROUP' && this.hasGroupEmailsTarget) {
            this.groupEmailsTarget.classList.remove('hidden');
        }
    }
}
