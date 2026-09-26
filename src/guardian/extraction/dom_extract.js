// Script injected by Playwright to extract text nodes and their styles
function extractNodes() {
    const results = [];
    
    const BLOCK_ELEMENTS = new Set([
        'DIV', 'P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'UL', 'OL', 'LI', 
        'TABLE', 'TR', 'TD', 'TH', 'ARTICLE', 'SECTION', 'BLOCKQUOTE', 
        'FIGURE', 'FIGCAPTION', 'HEADER', 'FOOTER', 'MAIN', 'NAV', 'ASIDE', 
        'DD', 'DL', 'DT', 'HR', 'PRE', 'FORM', 'FIELDSET', 'BODY'
    ]);

    function isBlockElement(node) {
        return BLOCK_ELEMENTS.has(node.tagName.toUpperCase());
    }

    // Generate concise unique selector
    function generateUniqueSelector(el) {
        if (!el || !el.tagName) return '';
        if (el.tagName.toLowerCase() === 'html') return 'html';
        if (el.tagName.toLowerCase() === 'body') return 'body';

        function buildNodeSelector(node) {
            let sel = node.tagName.toLowerCase();
            if (node.id) {
                try {
                    return sel + '#' + CSS.escape(node.id);
                } catch(e) {}
            }
            if (node.className && typeof node.className === 'string') {
                const classes = node.className.trim().split(/\s+/).filter(Boolean);
                if (classes.length > 0) {
                    try {
                        sel += '.' + classes.map(c => CSS.escape(c)).join('.');
                    } catch(e) {}
                }
            }
            return sel;
        }

        let current = el;
        let path = [];
        
        // Attempt 1: tag.class up the tree
        while (current && current.nodeType === Node.ELEMENT_NODE && current.tagName.toLowerCase() !== 'html') {
            let sel = buildNodeSelector(current);
            path.unshift(sel);
            
            let fullSelector = path.join(' > ');
            try {
                if (document.querySelectorAll(fullSelector).length === 1) {
                    return fullSelector;
                }
            } catch(e) {} // ignore invalid selectors
            
            current = current.parentElement;
        }

        // Attempt 2: fallback to nth-of-type for exact path
        current = el;
        path = [];
        while (current && current.nodeType === Node.ELEMENT_NODE && current.tagName.toLowerCase() !== 'html') {
            let sel = current.tagName.toLowerCase();
            
            const parent = current.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(child => child.tagName === current.tagName);
                if (siblings.length > 1) {
                    const index = siblings.indexOf(current) + 1;
                    sel += `:nth-of-type(${index})`;
                }
            }
            
            path.unshift(sel);
            let fullSelector = path.join(' > ');
            try {
                if (document.querySelectorAll(fullSelector).length === 1) {
                    return fullSelector;
                }
            } catch(e) {}
            
            current = current.parentElement;
        }
        
        return path.join(' > ');
    }

    // Calculate effective styles
    function getEffectiveStyles(el) {
        let current = el;
        let effectiveOpacity = 1.0;
        let effectiveBg = 'rgba(0, 0, 0, 0)'; // transparent by default
        
        while (current && current.nodeType === Node.ELEMENT_NODE) {
            const st = window.getComputedStyle(current);
            
            // Multiply opacities
            if (st.opacity !== '') {
                effectiveOpacity *= parseFloat(st.opacity);
            }
            
            // Find first non-transparent background
            if (effectiveBg === 'rgba(0, 0, 0, 0)' || effectiveBg === 'transparent') {
                if (st.backgroundColor !== 'rgba(0, 0, 0, 0)' && st.backgroundColor !== 'transparent') {
                    effectiveBg = st.backgroundColor;
                }
            }
            
            current = current.parentElement;
        }
        
        return {
            effective_opacity: effectiveOpacity.toString(),
            effective_background_color: effectiveBg
        };
    }

    // Text Segmentation: Find lowest-level block elements or elements that only contain text/inline nodes
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
        // Skip script, style, etc.
        if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'IFRAME', 'SVG'].includes(el.tagName.toUpperCase())) {
            continue;
        }

        // Check if element has any block-level children
        let hasBlockChildren = false;
        for (const child of el.children) {
            if (isBlockElement(child)) {
                hasBlockChildren = true;
                break;
            }
        }

        if (hasBlockChildren) {
            continue;
        }

        // Extract text content. textContent gets all text inside, ignoring HTML tags (combines spans).
        const text = el.textContent || '';
        const trimmedText = text.replace(/\s+/g, ' ').trim();
        
        if (trimmedText.length === 0) {
            continue;
        }

        const styles = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        const effective = getEffectiveStyles(el);
        
        results.push({
            text: text, // Keep original whitespace for python to process
            tag_name: el.tagName.toLowerCase(),
            classes: Array.from(el.classList),
            computed_styles: {
                'display': styles.display,
                'opacity': styles.opacity,
                'effective_opacity': effective.effective_opacity,
                'color': styles.color,
                'background-color': styles.backgroundColor,
                'effective_background_color': effective.effective_background_color,
                'font-size': styles.fontSize,
                'position': styles.position,
                'left': styles.left,
                'top': styles.top,
                'text-indent': styles.textIndent,
                'visibility': styles.visibility,
                'clip': styles.clip
            },
            bounding_rect: {
                'x': rect.x,
                'y': rect.y,
                'width': rect.width,
                'height': rect.height
            },
            location_selector: generateUniqueSelector(el)
        });
    }
    
    return results;
}
