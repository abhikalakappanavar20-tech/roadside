/**
 * Roadside Assist - Main JavaScript File
 * Contains utility functions and common functionality
 */

// Roadside Assist Namespace
const RoadsideAssist = (function() {
    'use strict';

    // Private variables
    let map = null;
    let userMarker = null;
    let providerMarkers = [];

    // Configuration
    const config = {
        refreshInterval: 5000, // 5 seconds
        notificationSound: null,
        currentLocation: null
    };

    // Utility Functions
    const utils = {
        /**
         * Get CSRF token from cookies
         */
        getCSRFToken: function() {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.startsWith('csrftoken=')) {
                        cookieValue = decodeURIComponent(cookie.substring('csrftoken='.length));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        /**
         * Format date to relative time
         */
        timeAgo: function(date) {
            const seconds = Math.floor((new Date() - new Date(date)) / 1000);

            if (seconds < 60) return 'Just now';
            if (seconds < 3600) return Math.floor(seconds / 60) + ' min ago';
            if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
            return Math.floor(seconds / 86400) + ' days ago';
        },

        /**
         * Format currency
         */
        formatCurrency: function(amount) {
            return '₹' + parseFloat(amount).toFixed(2);
        },

        /**
         * Debounce function
         */
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    };

    // Geolocation Functions
    const geolocation = {
        /**
         * Get user's current location
         */
        getCurrentPosition: function() {
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error('Geolocation is not supported'));
                    return;
                }

                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const location = {
                            lat: position.coords.latitude,
                            lng: position.coords.longitude,
                            accuracy: position.coords.accuracy
                        };
                        config.currentLocation = location;
                        resolve(location);
                    },
                    (error) => {
                        let errorMessage = 'Unable to retrieve location';
                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                errorMessage = 'Location access denied. Please enable location services.';
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMessage = 'Location information unavailable.';
                                break;
                            case error.TIMEOUT:
                                errorMessage = 'Location request timed out.';
                                break;
                        }
                        reject(new Error(errorMessage));
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
            });
        },

        /**
         * Watch position changes
         */
        watchPosition: function(callback) {
            if (!navigator.geolocation) {
                console.error('Geolocation not supported');
                return;
            }

            return navigator.geolocation.watchPosition(
                (position) => {
                    callback({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    });
                },
                (error) => {
                    console.error('Error watching position:', error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 5000
                }
            );
        },

        /**
         * Calculate distance between two coordinates (in km)
         */
        calculateDistance: function(lat1, lon1, lat2, lon2) {
            const R = 6371; // Earth's radius in km
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                      Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return R * c;
        }
    };

    // Map Functions (Leaflet)
    const maps = {
        /**
         * Initialize map
         */
        initMap: function(elementId, options = {}) {
            if (typeof L === 'undefined') {
                console.error('Leaflet is not loaded');
                return null;
            }

            const defaultOptions = {
                center: [20.5937, 78.9629],
                zoom: 5
            };

            map = L.map(elementId, {...defaultOptions, ...options});

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(map);

            return map;
        },

        /**
         * Add marker to map
         */
        addMarker: function(lat, lng, options = {}) {
            if (!map) return null;

            const defaultOptions = {
                draggable: false
            };

            const marker = L.marker([lat, lng], {...defaultOptions, ...options}).addTo(map);

            if (options.popupContent) {
                marker.bindPopup(options.popupContent);
            }

            return marker;
        },

        /**
         * Update user location marker
         */
        updateUserLocation: function(lat, lng) {
            if (!map) {
                console.warn('Map not initialized');
                return;
            }

            if (userMarker) {
                userMarker.setLatLng([lat, lng]);
            } else {
                userMarker = L.marker([lat, lng], {
                    icon: L.divIcon({
                        className: 'user-marker',
                        html: '<div style="background: #dc3545; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>',
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    })
                }).addTo(map);
            }

            map.setView([lat, lng], 16);
        },

        /**
         * Draw route between two points
         */
        drawRoute: function(fromLat, fromLng, toLat, toLng) {
            if (!map) return;

            L.polyline([[fromLat, fromLng], [toLat, toLng]], {
                color: '#007bff',
                weight: 4,
                opacity: 0.7,
                dashArray: '10, 10'
            }).addTo(map);

            // Fit map to show both points
            map.fitBounds([[fromLat, fromLng], [toLat, toLng]], { padding: [50, 50] });
        },

        /**
         * Open location in external maps app
         */
        openInMaps: function(lat, lng, label = 'Destination') {
            const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
            window.open(url, '_blank');
        }
    };

    // API Functions
    const api = {
        /**
         * Make API request
         */
        request: function(endpoint, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': utils.getCSRFToken()
                }
            };

            return fetch(endpoint, {...defaultOptions, ...options})
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                });
        },

        /**
         * Get pending requests for providers
         */
        getPendingRequests: function() {
            return this.request('/api/pending-requests/');
        },

        /**
         * Accept a service request
         */
        acceptRequest: function(requestId) {
            return this.request(`/api/accept/${requestId}/`, {
                method: 'POST'
            });
        },

        /**
         * Get provider's active requests
         */
        getMyRequests: function() {
            return this.request('/api/my-requests/');
        },

        /**
         * Get customer's requests
         */
        getCustomerRequests: function() {
            return this.request('/api/customer-requests/');
        },

        /**
         * Update request status
         */
        updateRequestStatus: function(requestId, status) {
            return this.request(`/api/update-status/${requestId}/`, {
                method: 'POST',
                body: JSON.stringify({ status: status })
            });
        },

        /**
         * Update provider location
         */
        updateProviderLocation: function(lat, lng) {
            return this.request('/api/update-location/', {
                method: 'POST',
                body: JSON.stringify({ latitude: lat, longitude: lng })
            });
        }
    };

    // UI Functions
    const ui = {
        /**
         * Show notification
         */
        showNotification: function(message, type = 'info') {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            document.body.appendChild(alertDiv);

            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        },

        /**
         * Show loading spinner
         */
        showLoading: function(elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                element.innerHTML = `
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                `;
            }
        },

        /**
         * Hide loading spinner
         */
        hideLoading: function(elementId, content = '') {
            const element = document.getElementById(elementId);
            if (element) {
                element.innerHTML = content;
            }
        },

        /**
         * Confirm action
         */
        confirmAction: function(message, callback) {
            if (confirm(message)) {
                callback();
            }
        }
    };

    // Notification Sound
    const notifications = {
        /**
         * Play notification sound
         */
        play: function() {
            try {
                // Simple beep using Web Audio API
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();

                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);

                oscillator.frequency.value = 800;
                oscillator.type = 'sine';

                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.5);
            } catch (e) {
                console.warn('Could not play notification sound:', e);
            }
        },

        /**
         * Request notification permission
         */
        requestPermission: function() {
            if ('Notification' in window && Notification.permission === 'default') {
                Notification.requestPermission();
            }
        },

        /**
         * Show browser notification
         */
        show: function(title, body, icon = '') {
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(title, {
                    body: body,
                    icon: icon
                });
            }
        }
    };

    // Auto-refresh functionality
    const autoRefresh = {
        intervalId: null,

        /**
         * Start auto-refresh
         */
        start: function(callback, interval = config.refreshInterval) {
            this.stop();
            callback(); // Initial call
            this.intervalId = setInterval(callback, interval);
        },

        /**
         * Stop auto-refresh
         */
        stop: function() {
            if (this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            }
        }
    };

    // Public API
    return {
        config: config,
        utils: utils,
        geolocation: geolocation,
        maps: maps,
        api: api,
        ui: ui,
        notifications: notifications,
        autoRefresh: autoRefresh
    };
})();

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Request notification permission
    RoadsideAssist.notifications.requestPermission();

    // Add event listeners for common elements
    const refreshButtons = document.querySelectorAll('[data-refresh]');
    refreshButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const target = this.dataset.refresh;
            if (target && window.refreshFunctions && window.refreshFunctions[target]) {
                window.refreshFunctions[target]();
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-dismissible):not(.profile-info-box):not(.no-auto-hide)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RoadsideAssist;
}
