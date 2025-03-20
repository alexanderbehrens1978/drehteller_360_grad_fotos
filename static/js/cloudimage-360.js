/*!
 * 360 degree Image Slider v2.0.1
 * http://cloudimage.io
 *
 * Angepasst für die lokale Verwendung im 360° Drehteller Steuerungssystem
 * Basierend auf der js-cloudimage-360-view von Scaleflex
 */

(function() {
  'use strict';

  window.CI360 = {
    instances: [],
    numLoaded: 0,
    notInitOnLoad: false,
    disableAutoInit: false
  };

  const ATTR_NAMES = {
    folder: 'data-folder',
    filename: 'data-filename',
    imageCount: 'data-image-count',
    imageList: 'data-image-list',
    lazyload: 'data-lazyload',
    lazySelector: 'data-lazyload-selector',
    spinReverse: 'data-spin-reverse',
    speed: 'data-spin-speed',
    dragSpeed: 'data-drag-speed',
    keys: 'data-keys',
    boxShadow: 'data-box-shadow',
    bottomCircle: 'data-bottom-circle',
    fullScreen: 'data-fullscreen',
    magnifier: 'data-magnifier',
    magnifyFactor: 'data-magnify-factor',
    ratio: 'data-ratio',
    autoplay: 'data-autoplay',
    autoplayReverse: 'data-autoplay-reverse',
    autoplaySpeed: 'data-autoplay-speed',
    stopAutoplayOnClick: 'data-stop-autoplay-on-click',
    controlReverse: 'data-control-reverse',
    alt: 'data-alt',
    static: 'data-static',
    bottomCircleOffset: 'data-bottom-circle-offset',
    initOnLoad: 'data-init-on-load'
  };

  class CI360Viewer {
    constructor(container, options) {
      this.container = container;
      this.activeImage = 1;
      this.movementStart = 0;
      this.isClicked = false;
      this.loadedImages = 0;
      this.imagesLoaded = false;
      this.reversed = false;
      this.dragSpeed = 150;
      this.autoplaySpeed = 10;
      this.bottomCircleOffset = 5;
      this.keys = {
        left: [37, 65],
        right: [39, 68]
      };
      this.init(options);
      return this;
    }

    mousedown(event) {
      if (this.imageData.length === 1) {
        return;
      }

      event.preventDefault();

      if (this.autoplay) {
        this.stop();
        if (this.stopAutoplayOnClick) {
          this.autoplay = false;
        }
      }

      if (this.view360Icon) {
        this.remove360ViewIcon();
      }

      if (this.magnifier && this.magnify) {
        this.closeMagnifier();
      }

      if (event.type === 'mousedown') {
        this.movementStart = event.pageX;
      } else {
        this.movementStart = event.touches[0].pageX;
      }

      this.isClicked = true;
    }

    mouseup() {
      if (this.imageData.length === 1) {
        return;
      }

      this.isClicked = false;
    }

    mousemove(event) {
      if (this.imageData.length === 1) {
        return;
      }

      if (this.isClicked) {
        let eventX;
        if (event.type === 'mousemove') {
          eventX = event.pageX;
        } else {
          eventX = event.touches[0].pageX;
        }

        const movementDistance = Math.abs(eventX - this.movementStart);

        if (movementDistance > this.dragSpeed) {
          this.movementStart = eventX;

          if (this.spinReverse ? eventX < this.movementStart : eventX > this.movementStart) {
            this.moveActiveIndexDown();
          } else {
            this.moveActiveIndexUp();
          }
        }
      }
    }

    moveActiveIndexUp() {
      if (this.stopAtEdges) {
        if (this.activeImage === 1) {
          return;
        }
      }

      this.activeImage = this.activeImage === 1 ? this.imageData.length : this.activeImage - 1;
      this.update();
    }

    moveActiveIndexDown() {
      if (this.stopAtEdges) {
        if (this.activeImage === this.imageData.length) {
          return;
        }
      }

      this.activeImage = this.activeImage === this.imageData.length ? 1 : this.activeImage + 1;
      this.update();
    }

    update() {
      this.image.src = this.imageData[this.activeImage - 1];
      if (this.fullScreenView) {
        this.fullScreenImage.src = this.imageData[this.activeImage - 1];
      }
    }

    loop(direction) {
      if (this.autoplay) {
        const loop = () => {
          if (!this.autoplay) {
            clearInterval(this.loopTimeoutId);
            return;
          }

          if (direction === 'right') {
            this.moveActiveIndexDown();
          } else {
            this.moveActiveIndexUp();
          }
        };

        this.loopTimeoutId = setInterval(loop, this.autoplaySpeed);
      }
    }

    play() {
      if (this.bottomCircle) {
        this.hide360ViewCircleIcon();
      }
      this.autoplay = true;
      this.loopTimeoutId = window.setInterval(
        () => this.loop(this.autoplayReverse ? 'left' : 'right'),
        this.autoplaySpeed
      );
    }

    stop() {
      if (this.bottomCircle) {
        this.show360ViewCircleIcon();
      }
      this.autoplay = false;
      window.clearTimeout(this.loopTimeoutId);
    }

    keyup(event) {
      if (!event.isTrusted) {
        return;
      }

      if (this.imageData.length === 1) {
        return;
      }

      const leftKeys = this.keys.left;
      const rightKeys = this.keys.right;

      if (leftKeys.includes(event.keyCode)) {
        this.moveActiveIndexUp();
      } else if (rightKeys.includes(event.keyCode)) {
        this.moveActiveIndexDown();
      }
    }

    loadImage(idx) {
      const image = new Image();
      image.src = this.imageData[idx];
      image.onload = () => {
        this.loadedImages += 1;
        if (this.loadedImages === this.imageData.length) {
          this.imagesLoaded = true;
          this.hideLoader();
          this.showImage();
          if (this.fullScreen) {
            this.addFullScreenControls();
          }
          if (this.autoplay) {
            this.play();
          }
          if (this.view360Icon) {
            this.add360ViewIcon();
          }
        }
      };
    }

    hideLoader() {
      if (this.loader) {
        this.loader.style.opacity = '0';
        window.setTimeout(() => {
          this.loader.remove();
          this.loader = null;
        }, 1000);
      }
    }

    add360ViewIcon() {
      const view360Icon = document.createElement('div');
      view360Icon.className = 'cloudimage-360-view-icon';
      view360Icon.style.position = 'absolute';
      view360Icon.style.top = '0';
      view360Icon.style.bottom = '0';
      view360Icon.style.left = '0';
      view360Icon.style.right = '0';
      view360Icon.style.width = '100px';
      view360Icon.style.height = '100px';
      view360Icon.style.margin = 'auto';
      view360Icon.style.backgroundColor = 'rgba(255,255,255,0.8)';
      view360Icon.style.borderRadius = '50%';
      view360Icon.style.boxShadow = 'rgb(255 255 255 / 50%) 0 0 4px';
      view360Icon.style.zIndex = '2';
      view360Icon.style.color = 'rgb(80,80,80)';
      view360Icon.style.textAlign = 'center';
      view360Icon.style.lineHeight = '100px';
      view360Icon.style.cursor = 'pointer';
      view360Icon.innerText = '360°';
      view360Icon.style.transition = 'opacity 0.3s';
      view360Icon.addEventListener('click', () => {
        this.remove360ViewIcon();
        if (this.autoplay) {
          this.play();
        }
      });
      
      this.view360Icon = view360Icon;
      this.innerBox.appendChild(view360Icon);
    }

    remove360ViewIcon() {
      if (this.view360Icon) {
        this.view360Icon.style.opacity = '0';
        window.setTimeout(() => {
          this.view360Icon.remove();
          this.view360Icon = null;
        }, 300);
      }
    }

    addFullScreenControls() {
      const fullScreenBtn = document.createElement('div');
      fullScreenBtn.className = 'cloudimage-360-fullscreen-button';
      fullScreenBtn.innerText = '⤢';
      fullScreenBtn.style.position = 'absolute';
      fullScreenBtn.style.top = '10px';
      fullScreenBtn.style.right = '10px';
      fullScreenBtn.style.fontSize = '24px';
      fullScreenBtn.style.color = 'white';
      fullScreenBtn.style.cursor = 'pointer';
      fullScreenBtn.style.zIndex = '2';
      fullScreenBtn.style.backgroundColor = 'rgba(0,0,0,0.3)';
      fullScreenBtn.style.borderRadius = '50%';
      fullScreenBtn.style.width = '40px';
      fullScreenBtn.style.height = '40px';
      fullScreenBtn.style.textAlign = 'center';
      fullScreenBtn.style.lineHeight = '40px';
      fullScreenBtn.addEventListener('click', this.openFullscreen.bind(this));

      this.innerBox.appendChild(fullScreenBtn);
      this.fullScreenBtn = fullScreenBtn;
    }

    magnify(event) {
      const thumbPos = this.findPos(this.image);
      const cursorPos = {
        x: event.pageX - thumbPos.x,
        y: event.pageY - thumbPos.y
      };
      const cursorPercent = {
        x: (cursorPos.x / this.image.clientWidth) * 100,
        y: (cursorPos.y / this.image.clientHeight) * 100
      };

      if (cursorPercent.x <= 0) {
        cursorPercent.x = 0;
      }

      if (cursorPercent.x >= 100) {
        cursorPercent.x = 100;
      }

      if (cursorPercent.y <= 0) {
        cursorPercent.y = 0;
      }

      if (cursorPercent.y >= 100) {
        cursorPercent.y = 100;
      }

      if (this.glass) {
        this.glass.style.background = `url("${this.imageData[this.activeImage - 1]}") no-repeat`;
        this.glass.style.backgroundSize = `${this.image.width * this.magnifyFactor}px ${this.image.height * this.magnifyFactor}px`;
        this.glass.style.backgroundPosition = `${-cursorPercent.x * this.magnifyFactor + 100}px ${-cursorPercent.y * this.magnifyFactor + 100}px`;
        this.glass.style.left = `${cursorPos.x - this.glass.width / 2}px`;
        this.glass.style.top = `${cursorPos.y - this.glass.height / 2}px`;
      }
    }

    closeMagnifier() {
      if (!this.glass) {
        return;
      }
      this.magnify = false;
      this.glass.remove();
      this.glass = null;
    }

    openMagnifier() {
      this.magnify = true;
      this.glass = document.createElement('div');
      this.glass.className = 'cloudimage-360-img-magnifier-glass';
      this.glass.style.position = 'absolute';
      this.glass.style.width = `${parseInt(this.magnifier.split('px')[0])}px`;
      this.glass.style.height = `${parseInt(this.magnifier.split('px')[0])}px`;
      this.glass.style.border = '5px solid #fff';
      this.glass.style.borderRadius = `${parseInt(this.magnifier.split('px')[0])}px`;
      this.glass.style.cursor = 'none';
      this.glass.style.zIndex = '1000';
      this.glass.style.backgroundRepeat = 'no-repeat';
      this.glass.style.backgroundSize = `${this.image.width * this.magnifyFactor}px ${this.image.height * this.magnifyFactor}px`;
      this.glass.style.boxShadow = '0 0 0 7px rgba(255, 255, 255, 0.85), 0 0 7px 7px rgba(0, 0, 0, 0.25), inset 0 0 40px 2px rgba(0, 0, 0, 0.25)';
      document.querySelector('.cloudimage-360').appendChild(this.glass);
    }

    findPos(obj) {
      let curleft = 0;
      let curtop = 0;

      if (obj.offsetParent) {
        do {
          curleft += obj.offsetLeft;
          curtop += obj.offsetTop;
        } while ((obj = obj.offsetParent));

        return { x: curleft, y: curtop };
      }
      return undefined;
    }

    startCloudimage360() {
      this.image = this.createImage();
      this.innerBox.appendChild(this.image);
      this.boxShadow && (this.innerBox.style.boxShadow = this.boxShadow);

      const { ciToken, ciSize, ciOperation, ciFilters } = this.responsive;
      
      if (this.lazyload && this.container.offsetParent === null) {
        this.lazyController = new IntersectionObserver(entries => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              this.init();
              this.lazyController.unobserve(entry.target);
            }
          });
        }, { rootMargin: "0px 0px 200px 0px" });
        this.lazyController.observe(this.container);
      } else {
        this.init();
      }
    }

    createLoader() {
      const loader = document.createElement('div');
      loader.className = 'cloudimage-360-loader';
      loader.style.position = 'absolute';
      loader.style.top = '0';
      loader.style.left = '0';
      loader.style.right = '0';
      loader.style.bottom = '0';
      loader.style.margin = 'auto';
      loader.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
      loader.style.zIndex = '1';
      loader.style.pointerEvents = 'none';
      loader.style.width = '120px';
      loader.style.height = '120px';
      loader.style.borderRadius = '50%';
      loader.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.15)';
      loader.style.display = 'flex';
      loader.style.alignItems = 'center';
      loader.style.justifyContent = 'center';
      loader.style.transition = 'opacity 0.3s';

      const circular = document.createElement('div');
      circular.className = 'cloudimage-360-loader-circular';
      circular.style.width = '50px';
      circular.style.height = '50px';
      circular.style.border = '2px solid rgba(0, 0, 0, 0.2)';
      circular.style.borderTop = '2px solid #3f51b5';
      circular.style.borderRadius = '50%';
      circular.style.animation = 'cloudimage-360-spin 2s linear infinite';

      // Add animation style
      const style = document.createElement('style');
      style.innerHTML = `
        @keyframes cloudimage-360-spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `;
      document.head.appendChild(style);

      loader.appendChild(circular);
      this.innerBox.appendChild(loader);

      return loader;
    }

    createImage() {
      const image = document.createElement('img');
      image.setAttribute('alt', this.alt);
      image.setAttribute('draggable', 'false');
      this.ratio && (image.style.maxWidth = image.style.width = '100%');
      image.style.position = 'relative';
      image.style.width = '100%';
      image.style.height = '100%';
      image.style.objectFit = 'contain';
      image.style.userSelect = 'none';
      image.style.display = 'none';  // Initially hidden until loading complete

      // Copy all attributes from original IMG to our new one
      if (this.container.tagName === 'IMG') {
        const attributes = this.container.attributes;
        for (let i = 0; i < attributes.length; i++) {
          const attribute = attributes[i];
          if (attribute.name !== 'src' && attribute.name !== 'alt') {
            image.setAttribute(attribute.name, attribute.value);
          }
        }
      }

      return image;
    }

    createInnerBox() {
      const innerBox = document.createElement('div');
      innerBox.className = 'cloudimage-360-inner-box';
      innerBox.style.position = 'relative';
      innerBox.style.width = '100%';
      innerBox.style.height = '100%';
      innerBox.style.cursor = 'grab';

      return innerBox;
    }

    createHotspots() {
      if (this.hotspots && this.hotspots.length) {
        const hotspotElements = Array.from(document.querySelectorAll('.cloudimage-360-hotspot'));
        hotspotElements.forEach(el => el.remove());
        
        this.hotspots.forEach((hotspot, index) => {
          const hotspotTemplate = document.createElement('div');
          hotspotTemplate.className = 'cloudimage-360-hotspot';
          hotspotTemplate.id = hotspot.id || `hotspot-${index}`;

          const tooltip = document.createElement('div');
          tooltip.className = 'cloudimage-360-hotspot-tooltip';
          tooltip.style.position = 'absolute';
          tooltip.style.top = '0';
          tooltip.style.left = '0';
          tooltip.style.transform = 'translateY(-100%)';
          tooltip.style.display = 'none';

          if (hotspot.tooltip) {
            tooltip.innerHTML = hotspot.tooltip;
          }

          hotspotTemplate.style.position = 'absolute';
          hotspotTemplate.style.width = '30px';
          hotspotTemplate.style.height = '30px';
          hotspotTemplate.style.borderRadius = '50%';
          hotspotTemplate.style.backgroundColor = 'rgba(66, 134, 244, 0.6)';
          hotspotTemplate.style.border = '3px solid #FFF';
          hotspotTemplate.style.boxShadow = '0 0 5px rgba(0,0,0,0.3)';
          hotspotTemplate.style.zIndex = '10';
          hotspotTemplate.style.cursor = 'pointer';
          hotspotTemplate.style.pointerEvents = 'all';
          hotspotTemplate.style.display = 'none';
          
          // Only show hotspots for current active image
          if (parseInt(hotspot.view, 10) === this.activeImage) {
            hotspotTemplate.style.display = 'block';
          }

          hotspotTemplate.style.left = `${hotspot.positionX}%`;
          hotspotTemplate.style.top = `${hotspot.positionY}%`;
          hotspotTemplate.style.transform = `translate(-50%, -50%)`;

          hotspotTemplate.addEventListener('click', () => {
            if (hotspot.link) {
              window.open(hotspot.link);
            }
          });

          hotspotTemplate.addEventListener('mouseover', () => {
            if (hotspot.tooltip) {
              tooltip.style.display = 'block';
            }
          });

          hotspotTemplate.addEventListener('mouseout', () => {
            tooltip.style.display = 'none';
          });

          this.innerBox.appendChild(hotspotTemplate);
          hotspotTemplate.appendChild(tooltip);
        });
      }
    }

    init(options) {
      // The container can be a selector string or a real DOM element
      this.options = options || {};

      // Support both old and new options keys
      // For compatibility with old versions
      const { folder, filename, imageList, amount, draggable = true } = this.options;
      
      if (this.container.tagName === 'IMG') {
        this.originalImage = this.container;
        const parentElement = this.container.parentElement;
        const wrapper = document.createElement('div');

        wrapper.className = this.container.className;
        wrapper.setAttribute('style', this.container.getAttribute('style'));
        wrapper.className = 'cloudimage-360 initialized';
        
        this.container.className = '';
        this.container.removeAttribute('style');
        
        this.container.parentElement.insertBefore(wrapper, this.container);
        wrapper.appendChild(this.container);
        this.container = wrapper;
      }

      this.innerBox = this.createInnerBox();
      this.container.appendChild(this.innerBox);
      
      this.loader = this.createLoader();
      
      // Read data attributes from container or options
      this.folder = this.container.getAttribute(ATTR_NAMES.folder) || folder || '';
      this.filename = this.container.getAttribute(ATTR_NAMES.filename) || filename || '';
      this.imageList = this.container.getAttribute(ATTR_NAMES.imageList) || imageList || '';
      this.imageCount = parseInt(this.container.getAttribute(ATTR_NAMES.imageCount) || amount || 0, 10);
      this.lazyLoad = this.container.getAttribute(ATTR_NAMES.lazyload) === 'true';
      this.lazySelector = this.container.getAttribute(ATTR_NAMES.lazySelector) || null;
      this.ratio = this.container.getAttribute(ATTR_NAMES.ratio) || this.ratio;
      this.spinReverse = this.container.getAttribute(ATTR_NAMES.spinReverse) === 'true';
      this.smoothPlaying = this.container.getAttribute(ATTR_NAMES.smoothPlaying) === 'true';
      this.draggable = this.container.getAttribute(ATTR_NAMES.draggable) === 'false' ? false : draggable;
      this.keys = this.container.getAttribute(ATTR_NAMES.keys) !== 'false';
      this.bottomCircle = this.container.getAttribute(ATTR_NAMES.bottomCircle) === 'true';
      this.magnifier = this.container.getAttribute(ATTR_NAMES.magnifier) || false;
      this.boxShadow = this.container.getAttribute(ATTR_NAMES.boxShadow) || '';
      this.bottomCircleOffset = parseInt(this.container.getAttribute(ATTR_NAMES.bottomCircleOffset) || this.bottomCircleOffset, 10);
      this.fullScreen = this.container.getAttribute(ATTR_NAMES.fullScreen) === 'true';
      this.magnifierSize = this.magnifier !== 'false' ? parseInt(this.magnifier, 10) : 0;
      this.magnifyFactor = parseInt(this.container.getAttribute(ATTR_NAMES.magnifyFactor) || 3, 10);
      this.speed = parseInt(this.container.getAttribute(ATTR_NAMES.speed) || 150, 10);
      this.dragSpeed = parseInt(this.container.getAttribute(ATTR_NAMES.dragSpeed) || this.dragSpeed, 10);
      this.autoplay = this.container.getAttribute(ATTR_NAMES.autoplay) === 'true';
      this.autoplayReverse = this.container.getAttribute(ATTR_NAMES.autoplayReverse) === 'true';
      this.stopAutoplayOnClick = this.container.getAttribute(ATTR_NAMES.stopAutoplayOnClick) === 'true';
      this.autoplaySpeed = parseInt(this.container.getAttribute(ATTR_NAMES.autoplaySpeed) || this.autoplaySpeed, 10);
      this.controlReverse = this.container.getAttribute(ATTR_NAMES.controlReverse) === 'true';
      this.stopAtEdges = this.container.getAttribute(ATTR_NAMES.stopAtEdges) === 'true';
      this.alt = this.container.getAttribute(ATTR_NAMES.alt) || 'Product 360 view';
      this.view360Icon = this.container.getAttribute(ATTR_NAMES.static) !== 'true';
      
      this.initData();
      
      if (draggable) {
        this.container.classList.add('initialized');
        this.initEvents();
      }
    }

    initData() {
      // Parse source options and prepare data
      this.imageData = [];

      if (this.imageList) {
        const imgs = this.imageList.split(',');
        const count = imgs.length;
        
        for (let i = 0; i < count; i++) {
          this.imageData.push(imgs[i]);
        }
      } else {
        for (let i = 1; i <= this.imageCount; i++) {
          let suffix = '';
          if (i < 10) {
            suffix = `00${i}`;
          } else if (i < 100) {
            suffix = `0${i}`;
          } else {
            suffix = `${i}`;
          }
          
          const fileName = this.filename.replace('{index}', suffix);
          const imageUrl = this.folder ? `${this.folder}/${fileName}` : fileName;
          this.imageData.push(imageUrl);
        }
      }

      for (let i = 0; i < this.imageData.length; i++) {
        this.loadImage(i);
      }
    }

    initEvents() {
      this.innerBox.addEventListener('mousedown', this.mousedown.bind(this));
      this.innerBox.addEventListener('mouseup', this.mouseup.bind(this));
      this.innerBox.addEventListener('mousemove', this.mousemove.bind(this));
      
      this.innerBox.addEventListener('touchstart', this.mousedown.bind(this), { passive: true });
      this.innerBox.addEventListener('touchend', this.mouseup.bind(this), { passive: true });
      this.innerBox.addEventListener('touchmove', this.mousemove.bind(this), { passive: true });
      
      if (this.keys) {
        document.addEventListener('keyup', this.keyup.bind(this));
      }
      
      if (this.magnifier) {
        this.image.addEventListener('mouseover', () => {
          if (!this.glass) {
            this.openMagnifier();
          }
          
          if (!this.glass || !this.magnify) return;
          
          this.glass.className = 'cloudimage-360-img-magnifier-glass';
          this.image.addEventListener('mousemove', this.magnify.bind(this));
        });
        
        this.image.addEventListener('mouseout', () => {
          this.closeMagnifier();
        });
      }

      if (this.bottomCircle) {
        this.add360ViewCircleIcon();
        
        if (this.fullScreen) {
          if (this.view360Icon) {
            this.view360Icon.addEventListener('click', () => {
              this.openFullscreen();
            });
          }
        }
      }
    }

    add360ViewCircleIcon() {
      const view360CircleIcon = document.createElement('div');
      view360CircleIcon.className = 'cloudimage-360-bottom-circle';
      view360CircleIcon.style.position = 'absolute';
      view360CircleIcon.style.width = '50px';
      view360CircleIcon.style.height = '50px';
      view360CircleIcon.style.bottom = `${this.bottomCircleOffset}px`;
      view360CircleIcon.style.left = '50%';
      view360CircleIcon.style.transform = 'translateX(-50%)';
      view360CircleIcon.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
      view360CircleIcon.style.borderRadius = '50%';
      view360CircleIcon.style.boxShadow = 'rgb(255 255 255 / 50%) 0 0 4px';
      view360CircleIcon.style.zIndex = '2';
      view360CircleIcon.style.color = 'rgb(80,80,80)';
      view360CircleIcon.style.textAlign = 'center';
      view360CircleIcon.style.lineHeight = '50px';
      view360CircleIcon.style.cursor = 'pointer';
      view360CircleIcon.style.fontSize = '16px';
      view360CircleIcon.innerText = '360°';
      
      this.view360CircleIcon = view360CircleIcon;
      this.innerBox.appendChild(view360CircleIcon);
      
      if (this.autoplay) {
        this.hide360ViewCircleIcon();
      }
    }

    hide360ViewCircleIcon() {
      if (this.view360CircleIcon) {
        this.view360CircleIcon.style.opacity = '0';
      }
    }

    show360ViewCircleIcon() {
      if (this.view360CircleIcon) {
        this.view360CircleIcon.style.opacity = '1';
      }
    }

    openFullscreen() {
      const fullscreenDiv = document.createElement('div');
      fullscreenDiv.className = 'cloudimage-360-fullscreen';
      fullscreenDiv.style.position = 'fixed';
      fullscreenDiv.style.top = '0';
      fullscreenDiv.style.left = '0';
      fullscreenDiv.style.width = '100%';
      fullscreenDiv.style.height = '100%';
      fullscreenDiv.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
      fullscreenDiv.style.zIndex = '1031';
      
      const closeBtn = document.createElement('div');
      closeBtn.className = 'cloudimage-360-fullscreen-close';
      closeBtn.innerHTML = '&times;';
      closeBtn.style.position = 'absolute';
      closeBtn.style.top = '20px';
      closeBtn.style.right = '20px';
      closeBtn.style.fontSize = '40px';
      closeBtn.style.color = 'white';
      closeBtn.style.cursor = 'pointer';
      closeBtn.style.zIndex = '2';
      
      const container = document.createElement('div');
      container.className = 'cloudimage-360-fullscreen-container';
      container.style.position = 'absolute';
      container.style.top = '50%';
      container.style.left = '50%';
      container.style.transform = 'translate(-50%, -50%)';
      container.style.maxWidth = '80%';
      container.style.maxHeight = '80%';
      
      const img = document.createElement('img');
      img.src = this.imageData[this.activeImage - 1];
      img.style.maxWidth = '100%';
      img.style.maxHeight = '100%';
      
      container.appendChild(img);
      fullscreenDiv.appendChild(closeBtn);
      fullscreenDiv.appendChild(container);
      document.body.appendChild(fullscreenDiv);
      
      this.fullScreenView = fullscreenDiv;
      this.fullScreenImage = img;
      
      closeBtn.addEventListener('click', this.closeFullscreen.bind(this));
      img.addEventListener('mousedown', this.mousedown.bind(this));
      img.addEventListener('mouseup', this.mouseup.bind(this));
      img.addEventListener('mousemove', this.mousemove.bind(this));
      
      img.addEventListener('touchstart', this.mousedown.bind(this), { passive: true });
      img.addEventListener('touchend', this.mouseup.bind(this), { passive: true });
      img.addEventListener('touchmove', this.mousemove.bind(this), { passive: true });
    }

    closeFullscreen() {
      if (this.fullScreenView) {
        document.body.removeChild(this.fullScreenView);
        this.fullScreenView = null;
        this.fullScreenImage = null;
      }
    }

    showImage() {
      if (this.image) {
        this.image.style.display = 'block';
      }
    }
  }

  function getAttributes(container) {
    const attributeNames = Object.values(ATTR_NAMES);
    const attributes = {};

    attributeNames.forEach(name => {
      attributes[name] = container.getAttribute(name);
    });

    return attributes;
  }

  function getContainerWidth(container) {
    return container.clientWidth || 0;
  }

  function createContainer(element) {
    const container = document.createElement('div');
    container.className = 'cloudimage-360';
    container.style.position = 'relative';
    container.style.width = '100%';
    container.style.maxWidth = '100%';
    container.style.margin = '0 auto';
    container.style.cursor = 'grab';

    if (element.getAttribute('id')) {
      container.setAttribute('id', element.getAttribute('id'));
    }

    // Copy the original class to the container
    if (element.classList) {
      [...element.classList].forEach(cls => {
        container.classList.add(cls);
      });
    }

    return container;
  }

  function initializeCloudimage360() {
    const autoInitElements = document.querySelectorAll('[data-ci-js-360-view]:not(.initialized)');
    
    autoInitElements.forEach(container => {
      const viewer = new CI360Viewer(container);
      window.CI360.instances.push(viewer);
    });
  }

  function reInitializeCloudimage360() {
    const oldInstances = window.CI360.instances;
    window.CI360.instances = [];

    oldInstances.forEach(viewer => {
      if (viewer.innerBox && viewer.innerBox.parentNode) {
        viewer.innerBox.parentNode.removeChild(viewer.innerBox);
      }
    });

    initializeCloudimage360();
  }

  window.CI360.init = function() {
    initializeCloudimage360();
  };

  if (!window.CI360.disableAutoInit && !window.CI360.notInitOnLoad) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initializeCloudimage360);
    } else {
      initializeCloudimage360();
    }
  }

  window.CI360.viewer = function(container, options) {
    return new CI360Viewer(container, options);
  };
})();
