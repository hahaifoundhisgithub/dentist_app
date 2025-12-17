// apps/core/static/core/js/global.js
// 全域 JavaScript - 所有頁面共用

/**
 * 頁面載入完成後執行
 */
document.addEventListener("DOMContentLoaded", function () {
    console.log("圖書管理系統已載入");
  
    // 移動端側邊欄切換功能
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileCloseButton = document.getElementById('mobile-close-button');
    const sidebar = document.getElementById('sidebar');
    const mobileOverlay = document.getElementById('mobile-overlay');

    function openSidebar() {
        if (sidebar && mobileOverlay) {
            sidebar.classList.remove('-translate-x-full');
            sidebar.classList.add('translate-x-0');
            mobileOverlay.classList.remove('hidden');
            document.body.style.overflow = 'hidden'; // 防止背景滾動
        }
    }

    function closeSidebar() {
        if (sidebar && mobileOverlay) {
            sidebar.classList.add('-translate-x-full');
            sidebar.classList.remove('translate-x-0');
            mobileOverlay.classList.add('hidden');
            document.body.style.overflow = ''; // 恢復滾動
        }
    }

    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', openSidebar);
    }

    if (mobileCloseButton) {
        mobileCloseButton.addEventListener('click', closeSidebar);
    }

    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', closeSidebar);
    }

    // 點擊側邊欄連結時，在移動端自動關閉側邊欄
    if (sidebar) {
        const sidebarLinks = sidebar.querySelectorAll('a');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', () => {
                // 只在移動端關閉
                if (window.innerWidth < 768) {
                    closeSidebar();
                }
            });
        });
    }

    // 視窗大小改變時，如果是桌面版則關閉移動端側邊欄
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 768) {
            closeSidebar();
        }
    });
  });
  