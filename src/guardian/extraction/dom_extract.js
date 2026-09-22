// Script injected by Playwright to extract text nodes and their styles
function extractNodes() {
    const results = [];
    
    // Function to compute absolute CSS selector
    function getCssSelector(el) {
        if (el.tagName.toLowerCase() === 'html') return 'html';
        if (el.tagName.toLowerCase() === 'body') return 'body';
        
        let selector = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') {
            const classes = el.className.trim().split(/\s+/).join('.');
            if (classes) {
                selector += '.' + classes;
            }
        }
        
        const parent = el.parentElement;
        if (!parent) return selector;
        
        const siblings = Array.from(parent.children).filter(child => child.tagName === el.tagName);
        if (siblings.length > 1) {
            const index = siblings.indexOf(el) + 1;
            selector += `:nth-of-type(${index})`;
        }
        
        return getCssSelector(parent) + ' > ' + selector;
    }

    const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode: function(node) {
                // Ignore script and style texts
                if (node.parentElement && ['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(node.parentElement.tagName)) {
                    return NodeFilter.FILTER_REJECT;
                }
                if (node.textContent.trim().length === 0) {
                    return NodeFilter.FILTER_REJECT;
                }
                return NodeFilter.FILTER_ACCEPT;
            }
        }
    );

    let currentNode;
    while (currentNode = walker.nextNode()) {
        const parent = currentNode.parentElement;
        if (!parent) continue;

        const styles = window.getComputedStyle(parent);
        const rect = parent.getBoundingClientRect();
        
        results.push({
            text: currentNode.textContent,
            tag_name: parent.tagName.toLowerCase(),
            classes: Array.from(parent.classList),
            computed_styles: {
                'display': styles.display,
                'opacity': styles.opacity,
                'color': styles.color,
                'font-size': styles.fontSize,
                'position': styles.position,
                'left': styles.left,
                'visibility': styles.visibility
            },
            bounding_rect: {
                'x': rect.x,
                'y': rect.y,
                'width': rect.width,
                'height': rect.height
            },
            location_selector: getCssSelector(parent)
        });
    }
    
    return results;
}
