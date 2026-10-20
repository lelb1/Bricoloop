:root { font-family: Inter, system-ui, Arial, sans-serif; color: #152b26; background: #f5f7f5; font-synthesis: none; }
* { box-sizing: border-box; }
body { margin: 0; }
.container { max-width: 1100px; margin: 0 auto; padding: 26px 22px 60px; }
.hero { padding: 28px 30px; border-radius: 20px; background: #164e3d; color: #fff; margin-bottom: 35px; }
.brand { font-weight: 800; font-size: 1.65rem; }
.hero p { margin: 8px 0 0; color: #d9eee5; }
h1 { font-size: clamp(1.7rem, 3vw, 2.2rem); margin: 0 0 8px; }
.intro { color: #53675e; margin: 0 0 24px; }
.tool-grid { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; }
.tool-card { border: 1px solid #dfe8e0; border-radius: 16px; background: #fff; padding: 20px; box-shadow: 0 3px 14px #142f1e0c; }
.tool-card-header { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; align-items: center; }
.category { font-size: .78rem; color: #617266; font-weight: 600; }
.status { display: inline-block; font-size: .77rem; font-weight: 700; padding: 6px 9px; border-radius: 99px; }
.available { color: #126b3b; background: #daf6e4; }
.lent { color: #935a05; background: #fff0ce; }
.unavailable { color: #7a3341; background: #fae2e5; }
.tool-card h2 { font-size: 1.2rem; margin: 22px 0 8px; }
.tool-card p { margin-bottom: 0; color: #53675e; }
.error { padding: 15px; border: 1px solid #dd8997; background: #fff0f2; border-radius: 9px; color: #762237; }
