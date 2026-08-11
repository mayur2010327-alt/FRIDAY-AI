async function sendMessage(){

    let input = document.getElementById("message");
    let chat = document.getElementById("chat");

    let message = input.value;

    if(message === "") return;


    chat.innerHTML += `
    <p><b>You:</b> ${message}</p>
    `;

    input.value = "";


    let response = await fetch(
        "http://127.0.0.1:8000/chat",
        {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                message:message
            })
        }
    );


    let data = await response.json();


    chat.innerHTML += `
    <p><b>FRIDAY:</b> ${data.reply}</p>
    `;


    chat.scrollTop = chat.scrollHeight;
}