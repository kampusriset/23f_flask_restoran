-- MySQL dump 10.13  Distrib 8.0.30, for Win64 (x86_64)
--
-- Host: localhost    Database: restaurant_db
-- ------------------------------------------------------
-- Server version	8.0.30

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `menu`
--

DROP TABLE IF EXISTS `menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `menu` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `category` varchar(50) NOT NULL,
  `price` int NOT NULL,
  `description` text,
  `image_url` varchar(255) DEFAULT NULL,
  `available` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `menu`
--

LOCK TABLES `menu` WRITE;
/*!40000 ALTER TABLE `menu` DISABLE KEYS */;
INSERT INTO `menu` VALUES (1,'Beef Bourguignon','Main Course',185000,'Daging sapi dimasak dengan red wine dan sayuran','https://images.unsplash.com/photo-1600891964092-4316c288032e?w=400',1,'2026-01-09 12:13:56'),(2,'Coq au Vin','Main Course',165000,'Ayam dalam saus wine merah dengan jamur','https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400',1,'2026-01-09 12:13:56'),(3,'Ratatouille','Main Course',125000,'Sayuran Prancis panggang dengan herbs','https://images.unsplash.com/photo-1572453800999-e8d2d1589b7c?w=400',1,'2026-01-09 12:13:56'),(4,'French Onion Soup','Appetizer',75000,'Sup bawang klasik dengan keju gruyere','https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400',1,'2026-01-09 12:13:56'),(5,'Escargots','Appetizer',95000,'Bekicot dengan garlic butter','https://usa.inquirer.net/files/2022/12/Authentic-Homemade-Escargots-Easy-Recipe.jpg',1,'2026-01-09 12:13:56'),(6,'Crème Brûlée','Dessert',65000,'Custard vanilla dengan karamel renyah','https://images.unsplash.com/photo-1470124182917-cc6e71b22ecc?w=400',1,'2026-01-09 12:13:56'),(7,'Tarte Tatin','Dessert',70000,'Tart apel karamel terbalik','https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400',1,'2026-01-09 12:13:56'),(8,'Galette de Bretagne','Appetizer',85000,'Panekuk dengan isian gurih dari Bretagne','https://cdn.tasteatlas.com/Images/Dishes/ba0206fa9d884c7dbbce4522a585805b.jpg?w=905&h=510',1,'2026-01-09 12:13:56'),(9,'Soufflé au Chocolat','Dessert',70000,'Kue cokelat ringan dan lembut','https://cdn.tasteatlas.com/images/dishes/ffe89104a97543eb80544c4e0b196bd5.jpg?w=905&h=510',1,'2026-01-09 12:13:56'),(10,'Créme Caramel','Dessert',65000,'Custard dengan krim karamel yang lembut','https://www.tasteatlas.com/Images/Dishes/e0fe68df68e5466e9a1d0f7580415820.jpg?mw=1300',1,'2026-01-09 12:13:56'),(11,'Confit de Canard','Main Course',123000,'Daging bebek super empuk','https://salsawisata.com/wp-content/uploads/2024/01/Confit-de-Canard.webp',1,'2026-01-09 12:13:56'),(12,'Langue de Bouef','Main Course',130000,'Lidah sapi dengan bumbu kuat','https://salsawisata.com/wp-content/uploads/2024/01/menu-makanan-khas-Perancis.webp',1,'2026-01-09 12:13:56'),(13,'Femboy','Main Course',999999,'Femboy asli bandung','/static/menu_images/Femboy_20260122203539_WhatsApp_Image_2025-11-30_at_20.55.50.jpeg',1,'2026-01-22 13:35:39');
/*!40000 ALTER TABLE `menu` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reservations`
--

DROP TABLE IF EXISTS `reservations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reservations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `date` date NOT NULL,
  `time` time NOT NULL,
  `guests` int NOT NULL,
  `message` text,
  `status` enum('pending','approved','rejected','completed') DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `reservations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reservations`
--

LOCK TABLES `reservations` WRITE;
/*!40000 ALTER TABLE `reservations` DISABLE KEYS */;
INSERT INTO `reservations` VALUES (1,3,'user1','user1@gmail.com','123','2026-01-23','12:12:00',2,'12','completed','2026-01-09 12:58:04'),(2,3,'user1','user1@gmail.com','123','2026-01-19','10:32:00',1,'','completed','2026-01-19 03:31:00'),(3,4,'user2','user2@gmail.com','123','2026-01-19','12:45:00',4,'','completed','2026-01-19 05:43:58'),(4,4,'user2','user2@gmail.com','123','2026-01-24','12:12:00',8,'','completed','2026-01-22 13:38:24'),(5,4,'user2','user2@gmail.com','123','2026-01-30','12:12:00',7,'','completed','2026-01-22 13:46:13'),(6,6,'user4','user4@gmail.com','123123','2026-02-12','12:12:00',2,'abcd','pending','2026-02-03 11:39:26'),(7,8,'user6','user6@gmail.com','123123','2026-02-04','12:12:00',2,'abcd','pending','2026-02-03 11:46:29'),(8,10,'user5','user5@gmail.com','123123','2026-02-05','12:12:00',3,'','pending','2026-02-03 12:08:41');
/*!40000 ALTER TABLE `reservations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `role` enum('admin','staff','customer') NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','scrypt:32768:8:1$qiBF3LcDt2lsjSSn$b79413afde07d5797608c830402df3865186615c5ca15003b0712df93bf646aa54dd0f3c5ac600094cc0d9eee57449ee2079aa5b16c861a1f2ad5d18b08701e6','admin@restaurant.com','admin','2026-01-09 12:13:56'),(2,'staff1','scrypt:32768:8:1$sfjH9Rwn8Pwpcut0$53a3d8d07578f0769e825ad7ee1b3867882449479f67b50e1fec67a151717c2d0470d0f1bc46591f33cb6d41316c1b44dc730b35bbecdfe2fa1ec99441869eac','staff1@restaurant.com','staff','2026-01-09 12:37:03'),(3,'user1','scrypt:32768:8:1$K8MjGLgEDsMtTU7P$6fdc8168829a7f19b47bc15fed2f826717a82b0f1d33c624ae26c37c4b5b23d27623afc133bcda51862a1d06b95caa0ebfc58fe3a90508a8c65911b6d426cbfd','user1@gmail.com','customer','2026-01-09 12:57:39'),(4,'user2','scrypt:32768:8:1$eVykUnAhDb8aQ0gi$85977ef27dd4204c6c9825f06bc512d42f09f6ad0a4c304bc23bb298b91109dc07b0b1502af86837c9e3b006e92b4d04941fe386e61172e69da1dd44079aa277','user2@gmail.com','customer','2026-01-19 05:43:25'),(5,'user3','scrypt:32768:8:1$nQRerXjWWKuxupFU$8d0d40749ddb22b69eb4075e5cb1055515345b5d227249e7b214c77fb70b066be200251fc17a5410af21a506889b60ecc355f993d57822e272383511b4470f8d','user3@gmail.com','customer','2026-02-03 11:33:14'),(6,'user4','scrypt:32768:8:1$wi7CDWcVER7tBl5f$041940818bbc81b46eec93b0d276d434968f76333ddad41cf7ca3223e0a098d47636d713529574cfee694f77b104daecc54ced6fe903c8125b2d260d99f79de3','user4@gmail.com','customer','2026-02-03 11:38:05'),(8,'user6','scrypt:32768:8:1$6h5yibffzhEEWqMH$1ece724414ec4e6b6c65151e5b6babce9ea8534f49627d0e0607ad017060f89c18f89734313c89d2ec7a29eb2b368fe1088dd9bfa5bad7da49b2fd50a77e295c','user6@gmail.com','customer','2026-02-03 11:45:19'),(10,'user5','scrypt:32768:8:1$YIVEeTO1PuSLFFbj$a516279b1bbf33c4f1b385ea7db06b6c470ed73fba8a1105cbbf40dae93819afec58c9b74eb98d239b8a185d67b7e90f78582e78c4a05e94318e7fe92ac01f35','user5@gmail.com','customer','2026-02-03 12:07:41');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-03 19:44:05
