class RichTextEditor {
    constructor(element, options = {}) {
        this.element = element;

        if (this.element._richtextInitialized) {
            return;
        }
        this.element._richtextInitialized = true;

        this.options = {
            placeholder: options.placeholder || 'Write something...',
            hiddenInput: options.hiddenInput,
            initialContent: options.initialContent || '',
        };
        this.init();
    }

    init() {
        if (this.element.previousElementSibling?.classList.contains('richtext-wrapper')) {
            return;
        }

        this.wrapper = document.createElement('div');
        this.wrapper.className = 'richtext-wrapper border border-input rounded-md overflow-hidden bg-background';

        this.toolbar = this.createToolbar();
        this.editor = this.createEditor();

        this.wrapper.appendChild(this.toolbar);
        this.wrapper.appendChild(this.editor);

        this.element.parentNode.insertBefore(this.wrapper, this.element);
        this.element.style.display = 'none';

        if (this.options.initialContent) {
            this.editor.innerHTML = this.options.initialContent;
        }

        this.setupEvents();

        requestAnimationFrame(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        });
    }

    createToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'richtext-toolbar flex items-center gap-1 p-2 border-b border-input bg-muted/30';

        const buttons = [
            { cmd: 'bold', icon: 'bold', title: 'Bold (Ctrl+B)' },
            { cmd: 'italic', icon: 'italic', title: 'Italic (Ctrl+I)' },
            { cmd: 'underline', icon: 'underline', title: 'Underline (Ctrl+U)' },
            { type: 'separator' },
            { cmd: 'insertUnorderedList', icon: 'list', title: 'Bullet List' },
            { cmd: 'insertOrderedList', icon: 'list-ordered', title: 'Numbered List' },
            { type: 'separator' },
            { cmd: 'formatBlock', value: 'h3', icon: 'heading', title: 'Heading' },
            { cmd: 'formatBlock', value: 'p', icon: 'pilcrow', title: 'Paragraph' },
        ];

        buttons.forEach(btn => {
            if (btn.type === 'separator') {
                const sep = document.createElement('div');
                sep.className = 'w-px h-5 bg-border mx-1';
                toolbar.appendChild(sep);
                return;
            }

            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'richtext-btn p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors';
            button.title = btn.title;
            button.innerHTML = `<i data-lucide="${btn.icon}" class="w-4 h-4"></i>`;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.execCommand(btn.cmd, btn.value);
            });
            toolbar.appendChild(button);
        });

        return toolbar;
    }

    createEditor() {
        const editor = document.createElement('div');
        editor.className = 'richtext-editor min-h-[120px] p-3 focus:outline-none prose prose-sm max-w-none';
        editor.contentEditable = true;
        editor.dataset.placeholder = this.options.placeholder;
        return editor;
    }

    setupEvents() {
        this.editor.addEventListener('input', () => this.syncToHiddenInput());
        this.editor.addEventListener('blur', () => this.syncToHiddenInput());

        this.editor.addEventListener('paste', (e) => {
            e.preventDefault();
            const text = e.clipboardData.getData('text/plain');
            document.execCommand('insertText', false, text);
        });

        this.editor.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key.toLowerCase()) {
                    case 'b':
                        e.preventDefault();
                        this.execCommand('bold');
                        break;
                    case 'i':
                        e.preventDefault();
                        this.execCommand('italic');
                        break;
                    case 'u':
                        e.preventDefault();
                        this.execCommand('underline');
                        break;
                }
            }
        });
    }

    execCommand(cmd, value = null) {
        this.editor.focus();
        document.execCommand(cmd, false, value);
        this.syncToHiddenInput();
        this.updateToolbarState();
    }

    updateToolbarState() {
        this.toolbar.querySelectorAll('.richtext-btn').forEach(btn => {
            const cmd = btn.dataset.cmd;
            if (cmd && document.queryCommandState(cmd)) {
                btn.classList.add('bg-muted', 'text-foreground');
            } else {
                btn.classList.remove('bg-muted', 'text-foreground');
            }
        });
    }

    syncToHiddenInput() {
        if (this.options.hiddenInput) {
            const input = document.querySelector(this.options.hiddenInput);
            if (input) {
                input.value = this.editor.innerHTML;
            }
        }
        this.element.value = this.editor.innerHTML;

        this.element.dispatchEvent(new Event('input', { bubbles: true }));
    }

    getContent() {
        return this.editor.innerHTML;
    }

    setContent(html) {
        this.editor.innerHTML = html;
        this.syncToHiddenInput();
    }
}

// Initialize richtext editors
function initializeRichTextEditors(container = document) {
    container.querySelectorAll('[data-richtext]:not([data-richtext-initialized])').forEach(el => {
        el.setAttribute('data-richtext-initialized', 'true');
        new RichTextEditor(el, {
            placeholder: el.getAttribute('placeholder') || 'Write something...',
            hiddenInput: el.dataset.richtextTarget,
            initialContent: el.value || '',
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initializeRichTextEditors();
});

document.addEventListener('htmx:afterSwap', (event) => {
    initializeRichTextEditors(event.detail.target);
});

if (typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) { // Element node
                    if (node.hasAttribute && node.hasAttribute('data-richtext')) {
                        initializeRichTextEditors(node.parentElement);
                    } else if (node.querySelectorAll) {
                        initializeRichTextEditors(node);
                    }
                }
            });
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

window.RichTextEditor = RichTextEditor;
window.initializeRichTextEditors = initializeRichTextEditors;
