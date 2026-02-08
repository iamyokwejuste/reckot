import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js";

export default class extends Controller {
  static targets = ["input", "preview", "noLogo", "overlay", "removeButton", "uploadButtonText", "removeFlag", "info"];
  static values = {
    maxWidth: { type: Number, default: 400 },
    maxHeight: { type: Number, default: 400 },
    quality: { type: Number, default: 0.9 },
  };

  connect() {
    if (this.hasInputTarget) {
      this.inputTarget.addEventListener("change", this.handleChange.bind(this));
    }
  }

  openFileInput() {
    if (this.hasInputTarget) {
      this.inputTarget.click();
    }
  }

  async handleChange(event) {
    const file = event.target.files[0];
    if (!file || !file.type.startsWith("image/")) return;

    try {
      const compressed = await this.compressImage(file);

      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(compressed);
      event.target.files = dataTransfer.files;

      this.showPreview(compressed);

      if (this.hasInfoTarget) {
        const reduction = ((1 - compressed.size / file.size) * 100).toFixed(0);
        const originalMb = (file.size / 1024 / 1024).toFixed(2);
        const compressedMb = (compressed.size / 1024 / 1024).toFixed(2);
        this.infoTarget.textContent = `${originalMb}MB → ${compressedMb}MB (${reduction}% smaller)`;
        this.infoTarget.classList.remove("hidden");
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

    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, width, height);
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
    if (this.hasPreviewTarget) {
      const url = URL.createObjectURL(file);
      this.previewTarget.src = url;
      this.previewTarget.classList.remove("hidden");
    }

    if (this.hasNoLogoTarget) {
      this.noLogoTarget.classList.add("hidden");
    }

    if (this.hasOverlayTarget) {
      this.overlayTarget.classList.remove("hidden");
    }

    if (this.hasRemoveButtonTarget) {
      this.removeButtonTarget.classList.remove("hidden");
    }

    if (this.hasUploadButtonTextTarget) {
      this.uploadButtonTextTarget.textContent = "Change";
    }

    if (this.hasRemoveFlagTarget) {
      this.removeFlagTarget.value = "false";
    }
  }

  removeLogo() {
    if (this.hasPreviewTarget) {
      this.previewTarget.src = "";
      this.previewTarget.classList.add("hidden");
    }

    if (this.hasNoLogoTarget) {
      this.noLogoTarget.classList.remove("hidden");
    }

    if (this.hasOverlayTarget) {
      this.overlayTarget.classList.add("hidden");
    }

    if (this.hasRemoveButtonTarget) {
      this.removeButtonTarget.classList.add("hidden");
    }

    if (this.hasUploadButtonTextTarget) {
      this.uploadButtonTextTarget.textContent = "Upload";
    }

    if (this.hasInputTarget) {
      this.inputTarget.value = "";
    }

    if (this.hasRemoveFlagTarget) {
      this.removeFlagTarget.value = "true";
    }

    if (this.hasInfoTarget) {
      this.infoTarget.classList.add("hidden");
    }
  }
}
