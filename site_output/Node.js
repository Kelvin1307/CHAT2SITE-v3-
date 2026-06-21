const express = require("express");
const fs = require("fs");
const app = express();

app.use(express.json());
app.use(express.static("site_output"));

app.post("/generate", (req, res) => {
  const data = req.body;

  const html = `
  <html>
  <head>
    <title>${data.store_name || "Store"}</title>
    <link rel="stylesheet" href="/style.css">
  </head>
  <body>
    <h1>${data.store_name || ""}</h1>
    <p>${data.tagline || ""}</p>
  </body>
  </html>
  `;

  fs.writeFileSync("site_output/index.html", html);
  res.send({ status: "generated" });
});

app.listen(3000, () => console.log("Server running on port 3000"));
