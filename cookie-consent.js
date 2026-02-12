/**
 * Cookie Consent Manager for The Crooked House
 * Standalone JavaScript implementation adapted from FFC template
 */

(function() {
  'use strict';

  // ============================================================================
  // CONFIGURATION - UPDATE THESE VALUES BEFORE PRODUCTION DEPLOYMENT
  // ============================================================================
  // TODO: Replace placeholder values with actual tracking IDs
  // Without valid IDs, analytics integrations will not function
  const CONFIG = {
    GA_MEASUREMENT_ID: 'G-XXXXXXXXXX',     // TODO: Add Google Analytics Measurement ID
    META_PIXEL_ID: 'XXXXXXXXXXXXXXX',      // TODO: Add Meta (Facebook) Pixel ID
    CLARITY_PROJECT_ID: 'XXXXXXXXXX',      // TODO: Add Microsoft Clarity Project ID
  };
  // ============================================================================

  // Helper to check if ID is a valid (non-placeholder) value
  function isValidTrackingId(id) {
    if (!id || id.length <= 5) {
      return false;
    }

    // Known placeholder values used in CONFIG
    const placeholderIds = [
      'G-XXXXXXXXXX',
      'XXXXXXXXXXXXXXX',
      'XXXXXXXXXX'
    ];

    if (placeholderIds.includes(id)) {
      return false;
    }

    // Treat values that are all/mostly 'X' (optionally after 'G-' prefix) as placeholders
    const normalized = id.startsWith('G-') ? id.slice(2) : id;
    if (/^X+$/i.test(normalized)) {
      return false;
    }

    return true;
  }

  // Cookie preferences object
  let preferences = {
    necessary: true,
    functional: true,
    analytics: false,
    marketing: false
  };

  let savedPreferencesBackup = {...preferences};
  let showBanner = false;
  let showPreferences = false;
  let previousFocusElement = null;
  let focusTrapHandler = null;

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    loadPreferencesFromStorage();
    createBannerHTML();
    attachEventListeners();
    
    // Expose global function to reopen preferences
    window.openCookiePreferences = openPreferences;
  }

  function loadPreferencesFromStorage() {
    try {
      const consent = localStorage.getItem('cookie-consent');
      if (!consent) {
        showBanner = true;
        return;
      }

      const savedData = JSON.parse(consent);
      
      // Check if consent has expired (12 months = 365 days)
      if (savedData.savedAt) {
        const savedDate = new Date(savedData.savedAt);
        const now = new Date();
        const daysSinceSaved = (now - savedDate) / (1000 * 60 * 60 * 24);
        
        if (daysSinceSaved > 365) {
          // Consent expired, clear and show banner
          localStorage.removeItem('cookie-consent');
          showBanner = true;
          return;
        }
      }
      
      if (validatePreferences(savedData)) {
        preferences = {...savedData, functional: true};
        savedPreferencesBackup = {...preferences};
        applyConsent(preferences);
      } else {
        showBanner = true;
      }
    } catch (e) {
      showBanner = true;
    }
  }

  function validatePreferences(prefs) {
    return (
      typeof prefs === 'object' &&
      prefs !== null &&
      typeof prefs.necessary === 'boolean' &&
      typeof prefs.analytics === 'boolean' &&
      typeof prefs.marketing === 'boolean'
    );
  }

  function createBannerHTML() {
    const container = document.createElement('div');
    container.id = 'cookie-consent-container';
    
    // Determine the correct path to cookie-policy.html based on current page location
    const currentPath = window.location.pathname;
    // Check if we're in a subdirectory (path has more than 2 segments: / + directory + file)
    const isInSubdirectory = currentPath.split('/').length > 2;
    const cookiePolicyPath = isInSubdirectory
      ? '../cookie-policy.html'
      : 'cookie-policy.html';
    
    container.innerHTML = `
      <div id="cookie-banner" class="cookie-banner" style="display: none;" role="region" aria-labelledby="cookie-banner-title">
        <div class="cookie-banner-content">
          <div class="cookie-banner-text">
            <h3 id="cookie-banner-title">We Value Your Privacy</h3>
            <p>
              We use cookies to improve your experience on our site, analyze traffic, and enable
              certain features. By clicking "Accept All", you consent to our use of
              cookies for analytics and marketing purposes. You can manage your preferences or
              decline non-essential cookies.
            </p>
            <div class="cookie-banner-links">
              <a href="${cookiePolicyPath}">Cookie Policy</a>
            </div>
          </div>
          <div class="cookie-banner-buttons">
            <button id="cookie-decline" class="cookie-btn cookie-btn-secondary">Decline All</button>
            <button id="cookie-customize" class="cookie-btn cookie-btn-secondary">Customize</button>
            <button id="cookie-accept" class="cookie-btn cookie-btn-primary">Accept All</button>
          </div>
        </div>
      </div>

      <div id="cookie-preferences" class="cookie-preferences-modal" style="display: none;" role="dialog" aria-modal="true" aria-labelledby="cookie-preferences-title">
        <div class="cookie-modal-overlay"></div>
        <div class="cookie-modal-content">
          <h2 id="cookie-preferences-title">Cookie Preferences</h2>
          <p>We use cookies to enhance your browsing experience and analyze our traffic. You can choose which types of cookies you allow.</p>
          
          <div class="cookie-category">
            <div class="cookie-category-header">
              <h3>Necessary Cookies</h3>
              <div class="cookie-toggle">
                <input type="checkbox" id="pref-necessary" checked disabled>
                <label for="pref-necessary">Always Active</label>
              </div>
            </div>
            <p class="cookie-category-desc">
              These cookies are essential for the website to function properly. They enable basic
              features like page navigation and access to secure areas.
            </p>
          </div>

          <div class="cookie-category">
            <div class="cookie-category-header">
              <h3>Functional Cookies</h3>
              <div class="cookie-toggle">
                <input type="checkbox" id="pref-functional" checked disabled>
                <label for="pref-functional">Always Active</label>
              </div>
            </div>
            <p class="cookie-category-desc">
              These cookies enable enhanced functionality and features that are essential for our core services.
            </p>
          </div>

          <div class="cookie-category">
            <div class="cookie-category-header">
              <h3>Analytics Cookies</h3>
              <div class="cookie-toggle">
                <input type="checkbox" id="pref-analytics" class="cookie-toggle-input" aria-label="Enable Analytics Cookies">
                <label for="pref-analytics" class="cookie-toggle-label">
                  <span class="cookie-toggle-slider"></span>
                </label>
              </div>
            </div>
            <p class="cookie-category-desc">
              These cookies help us understand how visitors interact with our website by
              collecting and reporting information anonymously.
            </p>
          </div>

          <div class="cookie-category">
            <div class="cookie-category-header">
              <h3>Marketing Cookies</h3>
              <div class="cookie-toggle">
                <input type="checkbox" id="pref-marketing" class="cookie-toggle-input" aria-label="Enable Marketing Cookies">
                <label for="pref-marketing" class="cookie-toggle-label">
                  <span class="cookie-toggle-slider"></span>
                </label>
              </div>
            </div>
            <p class="cookie-category-desc">
              These cookies are used to track visitors across websites to display relevant and engaging ads.
            </p>
          </div>

          <div class="cookie-modal-buttons">
            <button id="cookie-save-prefs" class="cookie-btn cookie-btn-primary">Save Preferences</button>
            <button id="cookie-cancel-prefs" class="cookie-btn cookie-btn-secondary">Cancel</button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(container);
    
    if (showBanner) {
      document.getElementById('cookie-banner').style.display = 'block';
    }
  }

  function attachEventListeners() {
    document.getElementById('cookie-accept').addEventListener('click', handleAcceptAll);
    document.getElementById('cookie-decline').addEventListener('click', handleDeclineAll);
    document.getElementById('cookie-customize').addEventListener('click', handleShowPreferences);
    document.getElementById('cookie-save-prefs').addEventListener('click', handleSavePreferences);
    document.getElementById('cookie-cancel-prefs').addEventListener('click', handleCancelPreferences);
    
    // Modal overlay click to close
    document.querySelector('.cookie-modal-overlay').addEventListener('click', handleCancelPreferences);
    
    // Escape key to close modal and focus trap
    focusTrapHandler = function(e) {
      if (showPreferences) {
        if (e.key === 'Escape') {
          handleCancelPreferences();
          return;
        }
        
        // Focus trap - keep focus within modal
        if (e.key === 'Tab') {
          const modal = document.getElementById('cookie-preferences');
          const focusableElements = modal.querySelectorAll(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
          );
          const firstElement = focusableElements[0];
          const lastElement = focusableElements[focusableElements.length - 1];
          
          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };
    document.addEventListener('keydown', focusTrapHandler);

    // Update preferences object when toggles change
    document.getElementById('pref-analytics').addEventListener('change', function(e) {
      preferences.analytics = e.target.checked;
    });
    document.getElementById('pref-marketing').addEventListener('change', function(e) {
      preferences.marketing = e.target.checked;
    });
  }

  function handleAcceptAll() {
    preferences = {
      necessary: true,
      functional: true,
      analytics: true,
      marketing: true
    };
    saveAndApply();
    hideBanner();
  }

  function handleDeclineAll() {
    preferences = {
      necessary: true,
      functional: true,
      analytics: false,
      marketing: false
    };
    deleteAnalyticsCookies();
    saveAndApply();
    hideBanner();
  }

  function handleShowPreferences() {
    savedPreferencesBackup = {...preferences};
    updatePreferencesUI();
    showPreferences = true;
    
    // Store currently focused element to restore later
    previousFocusElement = document.activeElement;
    
    document.getElementById('cookie-preferences').style.display = 'block';
    
    // Focus first interactive element in modal
    setTimeout(() => {
      const modal = document.getElementById('cookie-preferences');
      const focusableElements = modal.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
    }, 100);
  }

  function handleSavePreferences() {
    saveAndApply();
    hidePreferences();
    hideBanner();
  }

  function handleCancelPreferences() {
    preferences = {...savedPreferencesBackup};
    hidePreferences();
  }

  function updatePreferencesUI() {
    document.getElementById('pref-analytics').checked = preferences.analytics;
    document.getElementById('pref-marketing').checked = preferences.marketing;
  }

  function saveAndApply() {
    try {
      const dataToSave = {
        ...preferences,
        savedAt: new Date().toISOString()
      };
      localStorage.setItem('cookie-consent', JSON.stringify(dataToSave));
    } catch (e) {
      console.warn('Unable to save preferences to localStorage:', e);
    }
    applyConsent(preferences, savedPreferencesBackup);
    savedPreferencesBackup = {...preferences};
  }

  function hideBanner() {
    document.getElementById('cookie-banner').style.display = 'none';
    showBanner = false;
  }

  function hidePreferences() {
    document.getElementById('cookie-preferences').style.display = 'none';
    showPreferences = false;
    
    // Restore focus to previously focused element
    if (previousFocusElement) {
      previousFocusElement.focus();
      previousFocusElement = null;
    }
  }

  function openPreferences() {
    showBanner = true;
    document.getElementById('cookie-banner').style.display = 'block';
    handleShowPreferences();
  }

  function applyConsent(prefs, previousPrefs) {
    // Set cookie to indicate consent status
    const cookieValue = JSON.stringify(prefs);
    const secureFlag = window.location.protocol === 'https:' ? '; Secure' : '';
    document.cookie = `cookie-consent=${encodeURIComponent(cookieValue)}; path=/; max-age=31536000; SameSite=Lax${secureFlag}`;

    // Check if consent was withdrawn
    if (previousPrefs) {
      if ((previousPrefs.analytics && !prefs.analytics) || (previousPrefs.marketing && !prefs.marketing)) {
        deleteAnalyticsCookies();
        
        // Disable already-loaded trackers
        if (previousPrefs.analytics && !prefs.analytics) {
          disableAnalyticsTrackers();
        }
        if (previousPrefs.marketing && !prefs.marketing) {
          disableMarketingTrackers();
        }
      }
    }

    // Push consent update to GTM dataLayer
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      event: 'consent_update',
      functional_consent: prefs.functional ? 'granted' : 'denied',
      analytics_consent: prefs.analytics ? 'granted' : 'denied',
      marketing_consent: prefs.marketing ? 'granted' : 'denied'
    });

    // Load scripts based on consent
    if (prefs.analytics) {
      loadGoogleAnalytics();
      loadMicrosoftClarity();
    }
    if (prefs.marketing) {
      loadMetaPixel();
    }
  }

  function deleteAnalyticsCookies() {
    const cookiesToDelete = ['_ga', '_gid', '_fbp', 'fr', '_clck', '_clsk'];
    const hostname = window.location.hostname;
    const dotHostname = '.' + hostname;
    
    cookiesToDelete.forEach(function(name) {
      // Delete cookie without explicit domain
      document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      // Delete cookie scoped to the current hostname
      document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=' + hostname + ';';
      // Delete cookie scoped to the parent ".hostname" variant
      document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=' + dotHostname + ';';
    });

    // Delete dynamic _ga_* cookies
    document.cookie.split(';').forEach(function(cookie) {
      const cookieName = cookie.split('=')[0].trim();
      if (cookieName.startsWith('_ga_')) {
        // Delete cookie without explicit domain
        document.cookie = cookieName + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        // Delete cookie scoped to the current hostname
        document.cookie = cookieName + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=' + hostname + ';';
        // Delete cookie scoped to the parent ".hostname" variant
        document.cookie = cookieName + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=' + dotHostname + ';';
      }
    });
  }

  function disableAnalyticsTrackers() {
    // Disable Google Analytics if loaded
    if (window.gtag && CONFIG.GA_MEASUREMENT_ID) {
      // Update consent mode to denied
      window.gtag('consent', 'update', {
        'analytics_storage': 'denied'
      });
      
      // Set GA disable flag
      const gaDisableProperty = 'ga-disable-' + CONFIG.GA_MEASUREMENT_ID;
      window[gaDisableProperty] = true;
    }
    
    // Disable Microsoft Clarity if loaded
    if (window.clarity) {
      try {
        // Clarity doesn't have a direct disable API, but we can stop it from sending data
        window.clarity('consent', false);
      } catch (e) {
        // Clarity API might not support consent method, continue silently
      }
    }
  }

  function disableMarketingTrackers() {
    // Disable Meta Pixel if loaded
    if (window.fbq) {
      try {
        // Revoke consent for Meta Pixel
        window.fbq('consent', 'revoke');
      } catch (e) {
        // Meta Pixel API might not support consent method in all versions
      }
    }
  }

  function loadGoogleAnalytics() {
    if (document.querySelector('script[src*="googletagmanager.com/gtag"]')) return;
    
    if (!isValidTrackingId(CONFIG.GA_MEASUREMENT_ID)) {
      console.warn('[Cookie Consent] Google Analytics ID is not configured. Skipping GA script loading.');
      return;
    }
    
    const gaScript = document.createElement('script');
    gaScript.async = true;
    gaScript.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(CONFIG.GA_MEASUREMENT_ID);
    document.head.appendChild(gaScript);

    const gaConfigScript = document.createElement('script');
    const secureFlag = window.location.protocol === 'https:' ? ';Secure' : '';
    gaConfigScript.textContent = `
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', '${CONFIG.GA_MEASUREMENT_ID}', {
        'anonymize_ip': true,
        'cookie_flags': 'SameSite=Lax${secureFlag}'
      });
    `;
    document.head.appendChild(gaConfigScript);
  }

  function loadMetaPixel() {
    if (document.querySelector('script[src*="fbevents.js"]')) return;
    
    if (!isValidTrackingId(CONFIG.META_PIXEL_ID)) {
      console.warn('[Cookie Consent] Meta Pixel ID is not configured. Skipping Meta Pixel script loading.');
      return;
    }
    
    const fbScript = document.createElement('script');
    fbScript.textContent = `
      !function(f,b,e,v,n,t,s)
      {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
      n.callMethod.apply(n,arguments):n.queue.push(arguments)};
      if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
      n.queue=[];t=b.createElement(e);t.async=!0;
      t.src=v;s=b.getElementsByTagName(e)[0];
      s.parentNode.insertBefore(t,s)}(window, document,'script',
      'https://connect.facebook.net/en_US/fbevents.js');
      fbq('init', '${CONFIG.META_PIXEL_ID}');
      fbq('track', 'PageView');
    `;
    document.head.appendChild(fbScript);

    const fbNoScript = document.createElement('noscript');
    const img = document.createElement('img');
    img.height = 1;
    img.width = 1;
    img.style.display = 'none';
    img.src = 'https://www.facebook.com/tr?id=' + encodeURIComponent(CONFIG.META_PIXEL_ID) + '&ev=PageView&noscript=1';
    fbNoScript.appendChild(img);
    document.body.appendChild(fbNoScript);
  }

  function loadMicrosoftClarity() {
    if (document.querySelector('script[src*="clarity.ms"]')) return;
    
    if (!isValidTrackingId(CONFIG.CLARITY_PROJECT_ID)) {
      console.warn('[Cookie Consent] Microsoft Clarity ID is not configured. Skipping Clarity script loading.');
      return;
    }
    
    const clarityScript = document.createElement('script');
    clarityScript.textContent = `
      (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
      })(window, document, "clarity", "script", "${CONFIG.CLARITY_PROJECT_ID}");
    `;
    document.head.appendChild(clarityScript);
  }

})();
