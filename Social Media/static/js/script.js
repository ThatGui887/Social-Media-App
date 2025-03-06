// Helper function for making API calls
async function fetchAPI(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message);
    return data;
}

// Authentication functions
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const data = await fetchAPI('/register', {
            method: 'POST',
            body: JSON.stringify({
                username: document.getElementById('reg-username').value,
                email: document.getElementById('reg-email').value,
                password: document.getElementById('reg-password').value
            })
        });
        alert('Registration successful! Please login.');
    } catch (error) {
        alert(error.message);
    }
});

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const data = await fetchAPI('/login', {
            method: 'POST',
            body: JSON.stringify({
                email: document.getElementById('login-email').value,
                password: document.getElementById('login-password').value
            })
        });
        document.getElementById('auth-section').classList.add('hidden');
        document.getElementById('post-section').classList.remove('hidden');
        loadPosts();
    } catch (error) {
        alert(error.message);
    }
});

// Post functions
document.getElementById('post-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const data = await fetchAPI('/post', {
            method: 'POST',
            body: JSON.stringify({
                content: document.getElementById('post-content').value,
                media_url: document.getElementById('media-url').value,
                media_type: document.getElementById('media-type').value
            })
        });
        document.getElementById('post-form').reset();
        loadPosts();
    } catch (error) {
        alert(error.message);
    }
});

async function loadPosts() {
    try {
        const posts = await fetchAPI('/posts');
        const container = document.getElementById('posts-container');
        container.innerHTML = posts.map(post => `
            <div class="post">
                <p>${post.content}</p>
                ${post.media_url ? renderMedia(post.media_url, post.media_type) : ''}
                <button onclick="likePost(${post.id})">Like</button>
                <div class="comments">
                    <form onsubmit="return addComment(event, ${post.id})">
                        <input type="text" placeholder="Add a comment" required>
                        <button type="submit">Comment</button>
                    </form>
                </div>
            </div>
        `).join('');
    } catch (error) {
        alert(error.message);
    }
}

function renderMedia(url, type) {
    if (type === 'photo') {
        return `<img src="${url}" alt="Post image" style="max-width: 100%;">`;
    } else if (type === 'video') {
        return `<video src="${url}" controls style="max-width: 100%;"></video>`;
    }
    return '';
}

async function likePost(postId) {
    try {
        await fetchAPI(`/post/${postId}/like`, { method: 'POST' });
        loadPosts();
    } catch (error) {
        alert(error.message);
    }
}

async function addComment(event, postId) {
    event.preventDefault();
    const input = event.target.querySelector('input');
    try {
        await fetchAPI(`/post/${postId}/comment`, {
            method: 'POST',
            body: JSON.stringify({ content: input.value })
        });
        input.value = '';
        loadPosts();
    } catch (error) {
        alert(error.message);
    }
    return false;
} 

function acceptRequest(requestId) {
    fetch(`/accept_request/${requestId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById(`request-${requestId}`).remove();
            location.reload();
        } else {
            alert(data.error || 'An error occurred');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred');
    });
}