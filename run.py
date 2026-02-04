from app import create_app

app = create_app()

if __name__ == "__main__":
    print("🔐 HUMA-RH v5 SECURE démarre sur http://127.0.0.1:5000")
    print("👤 Login: admin | Mot de passe: admin123")
    app.run(debug=True, port=5000)
