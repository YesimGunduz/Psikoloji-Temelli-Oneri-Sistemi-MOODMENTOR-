<?php
// veritabanı bağlantısı
$host   = 'localhost';
$db     = 'uzmanSistemDB';
$user   = 'root';
$pass   = 'root';
$charset= 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db;charset=$charset";
try {
    $pdo = new PDO($dsn, $user, $pass, [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
} catch (PDOException $e) {
    die("Veritabanı bağlantı hatası: " . $e->getMessage());
}

// soruları çekmek için sorgu
$stmt = $pdo->query("SELECT * FROM sorular ORDER BY id ASC");
$sorular = $stmt->fetchAll();
?>

<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Mood Mentor Öneri Sistemi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- Bootstrap CSS -->
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">

    <style>
        body {
            background-image: url('arkaplan.jpeg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            min-height: 100vh;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }

        .logo-box {
            position: absolute;
            top: 120px; 
            left: 40px;
            max-width: 320px;
            border-radius: 70%;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
        }
        .logo-box img {
            width: 100%; 
            height: auto;
            border-radius: 50%;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
        }
        .overlay {
            background-color: rgba(255, 255, 255, 0.5);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .form-box {
            background-color: #f7faff;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 0 25px rgba(0, 0, 0, 0.4);
            width: 100%;
            max-width: 750px;
        }

        h2 {
            text-align: center;
            margin-bottom: 30px;
            color: #007bff;
        }

        label {
            font-weight: bold;
        }

        .btn-submit {
            margin-top: 25px;
        }
    </style>
</head>
<body>


    <div class="logo-box">
        <img src="uzman_sistem_logo.jpg" alt="Mood Mentor Logo" class="img-fluid">
    </div>

    <div class="overlay">
        <div class="form-box">
            <h2>Mood Mentor Öneri Sistemi</h2>
            <form action="submit.php" method="POST">
                <?php foreach ($sorular as $soru): ?>
                    <?php
                        $field = htmlspecialchars($soru['field_name']);
                        $text  = htmlspecialchars($soru['question_text']);
                        $opts  = explode(',', $soru['answer_options']);
                    ?>
                    <div class="form-group">
                        <label for="<?= $field ?>"><?= $text ?></label>
                        <select name="<?= $field ?>" id="<?= $field ?>" class="form-control" required>
                            <?php foreach ($opts as $opt): ?>
                                <option value="<?= htmlspecialchars(trim($opt)) ?>"><?= htmlspecialchars(trim($opt)) ?></option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                <?php endforeach; ?>

                <button type="submit" class="btn btn-success btn-block btn-submit">Gönder</button>
            </form>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>

