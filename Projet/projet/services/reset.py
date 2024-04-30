from uuid import uuid4


p = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demande de réinitialisation de mot de passe</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            padding-top: 50px;
        }}
        .container {{
            max-width: 600px;
            margin: auto;
            padding: 20px;
            border-radius: 5px;
            background: #f8f9fa;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .link {{
            color: #007bff;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Demande de réinitialisation de mot de passe</h1>
        <p>Bonjour,</p>
        <p>Une demande de réinitialisation de mot de passe a été reçue pour votre compte. Si vous avez initié cette demande, veuillez suivre le lien ci-dessous pour réinitialiser votre mot de passe :</p>
        <p><a href="https://example.com/reset-password?token={0}" class="link">Réinitialiser mon mot de passe</a></p>
        <p>Si vous n'avez pas demandé à réinitialiser votre mot de passe, veuillez ignorer cet email. Aucune modification ne sera apportée à votre compte.</p>
        <p>Merci,</p>
        <p>Votre équipe de support</p>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
