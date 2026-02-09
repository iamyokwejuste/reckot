import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    download(event) {
        event.preventDefault()
        const link = event.currentTarget
        const filename = link.getAttribute("download") || "file"

        fetch(link.href)
            .then(r => r.blob())
            .then(blob => {
                const url = URL.createObjectURL(blob)
                const a = document.createElement("a")
                a.href = url
                a.download = filename
                document.body.appendChild(a)
                a.click()
                document.body.removeChild(a)
                URL.revokeObjectURL(url)
            })
    }
}
