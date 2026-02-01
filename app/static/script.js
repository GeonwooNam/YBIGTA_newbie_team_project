let userEmail = null;

function loginUser() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    fetch('/api/user/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(error => { throw new Error(error.detail); });
        }
        return response.json();
    })
    .then(data => {
        userEmail = email; // 로그인 성공 시 이메일 저장
        document.getElementById('username').textContent = `${data.data.username}!`; // 사용자 이름 표시
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('logged-in-screen').style.display = 'block';
    })
    .catch(error => alert(`Login failed: ${error.message}`));
}

function registerUser() {
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const username = document.getElementById('register-username').value;

    fetch('/api/user/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password, username })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(error => { throw new Error(error.detail); });
        }
        return response.json();
    })
    .then(() => alert(`Registration successful! Welcome, ${username}.`)) // 성공 메시지에 사용자 이름 표시
    .catch(error => alert(`Registration failed: ${error.message}`));
}

function updatePassword() {
    const newPassword = document.getElementById('update-password').value;

    fetch('/api/user/update-password', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: userEmail, new_password: newPassword })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(error => { throw new Error(error.detail); });
        }
        return response.json();
    })
    .then(() => alert(`Password successfully updated!`)) // 성공 메시지
    .catch(error => alert(`Password update failed: ${error.message}`));
}

function deleteUser() {
    if (!userEmail) {
        alert("No user is logged in.");
        return;
    }

    fetch('/api/user/delete', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: userEmail }) // 저장된 이메일 전송
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(error => { throw new Error(error.detail); });
        }
        return response.json();
    })
    .then(() => {
        alert(`User deleted successfully!`);
        document.getElementById('logged-in-screen').style.display = 'none';
        document.getElementById('login-screen').style.display = 'block';
        userEmail = null; // 이메일 초기화
    })
    .catch(error => alert(`Account deletion failed: ${error.message}`));
}

(() => {
  function getWrap(input) {
    return input.closest(".input-wrap");
  }

  function computeState(input) {
    const v = (input.value ?? "").trim();
    if (v === "") return "empty";

    // HTML5 내장 검증 사용:
    // type=email이면 이메일 형식 검사, required/minlength/pattern 등이 있으면 그것도 반영됨
    return input.checkValidity() ? "valid" : "invalid";
  }

  function updateOne(input) {
    const wrap = getWrap(input);
    if (!wrap) return;
    wrap.dataset.touched = "1";
    wrap.dataset.state = computeState(input);
  }

  function touchOne(input) {
    const wrap = getWrap(input);
    if (!wrap) return;
    wrap.dataset.touched = "1";
  }

  function initInput(input) {
    // 입력 중엔 상태만 갱신(아이콘 노출은 touched=1 이후 CSS가 결정)
    input.addEventListener("input", () => updateOne(input));

    // blur되면 touched 처리 + 상태 갱신
    input.addEventListener("blur", () => {
      touchOne(input);
      updateOne(input);
    });

    // 자동완성/기존 값(새로고침 후 유지 등) 반영
    updateOne(input);
  }

  function touchAndUpdateForm(form) {
    const inputs = form.querySelectorAll(".input-wrap input");
    inputs.forEach((inp) => {
      touchOne(inp);
      updateOne(inp);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    // 1) 모든 input-wrap input에 대해 초기화
    document.querySelectorAll(".input-wrap input").forEach(initInput);

    // 2) 로그인/회원가입 버튼 클릭 시 전체 touched 처리(아이콘 한 번에 보이게)
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const updateForm = document.getElementById("update-password-section");

    if (loginForm) {
        const btn = loginForm.querySelector('button[onclick*="loginUser"]');
        if (btn) btn.addEventListener("click", () => touchAndUpdateForm(loginForm));
    }

    if (registerForm) {
        const btn = registerForm.querySelector('button[onclick*="registerUser"]');
        if (btn) btn.addEventListener("click", () => touchAndUpdateForm(registerForm));
    }

    if (updateForm) {
        const btn = registerForm.querySelector('button[onclick*="updatePassword"]');
        if (btn) btn.addEventListener("click", () => touchAndUpdateForm(updateForm));
    }

    // 3) 크롬 자동완성은 로드 직후 늦게 들어오는 경우가 있어 한번 더
    setTimeout(() => {
        document.querySelectorAll(".input-wrap input").forEach(updateOne);
    }, 80);
  });
})();