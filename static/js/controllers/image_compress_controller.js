import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js";

export default class extends Controller {
  static targets = ["input", "preview", "info"];
  static values = {
    maxWidth: { type: Number, default: 1200 },
    maxHeight: { type: Number, default: 630 },
    quality: { type: Number, default: 0.85 },
    maxSizeMb: { type: Number, default: 2 },
  };

  connect() {
    if (this.hasInputTarget) {
      this.inputTarget.addEventListener("change", this.compress.bind(this));
    }
  }

  async compress(event) {
    const file = event.target.files[0];
    if (!file || !file.type.startsWith("image/")) return;

    try {
      const compressed = await this.compressImage(file);
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(compressed);
      event.target.files = dataTransfer.files;

      if (this.hasPreviewTarget) {
        this.showPreview(compressed);
      }
    } catch (error) {
      console.error("Image compression failed:", error);
    }
  }

  async compressImage(file) {
    const img = await this.loadImage(file);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    let { width, height } = img;
    const aspectRatio = width / height;

    if (width > this.maxWidthValue) {
      width = this.maxWidthValue;
      height = width / aspectRatio;
    }

    if (height > this.maxHeightValue) {
      height = this.maxHeightValue;
      width = height * aspectRatio;
    }

    canvas.width = width;
    canvas.height = height;

    ctx.drawImage(img, 0, 0, width, height);

    const blob = await new Promise((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", this.qualityValue);
    });

    return new File([blob], file.name.replace(/\.\w+$/, ".jpg"), {
      type: "image/jpeg",
    });
  }

  loadImage(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = e.target.result;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  showPreview(file) {
    const url = URL.createObjectURL(file);
    this.previewTarget.src = url;
    this.previewTarget.classList.remove("hidden");
  }
}
