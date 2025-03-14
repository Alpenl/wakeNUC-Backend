-- 本项目已经去除MySQL数据库，使用SQLite内存数据库作为临时配置，之后若使用MySQL数据库，将此配置注释后打开mysql配置
SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for insider
-- ----------------------------
DROP TABLE IF EXISTS `insider`;
CREATE TABLE `insider` (
  `open_id` varchar(28) NOT NULL,
  `key` varchar(10) DEFAULT NULL,
  `expire_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `status` int(255) DEFAULT NULL,
  PRIMARY KEY (`open_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for news
-- ----------------------------
DROP TABLE IF EXISTS `news`;
CREATE TABLE `news` (
  `id` int(255) NOT NULL,
  `type` int(255) NOT NULL,
  `title` text,
  `publish_time` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `content` text,
  PRIMARY KEY (`id`,`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for notice
-- ----------------------------
DROP TABLE IF EXISTS `notice`;
CREATE TABLE `notice` (
  `id` int(255) NOT NULL,
  `标题` varchar(255) DEFAULT NULL,
  `时间` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `内容` text,
  `是否置顶` int(255) DEFAULT NULL COMMENT '1为置顶,0为不置顶',
  `重要` int(255) DEFAULT NULL,
  `发布者` varchar(25) DEFAULT NULL,
  `isshow` int(12) DEFAULT NULL,
  `ispop` int(12) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for slide
-- ----------------------------
DROP TABLE IF EXISTS `slide`;
CREATE TABLE `slide` (
  `id` int(255) NOT NULL,
  `index` int(255) DEFAULT NULL,
  `name` text,
  `image_url` text,
  `content` text,
  `isshow` int(12) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for vacation
-- ----------------------------
DROP TABLE IF EXISTS `vacation`;
CREATE TABLE `vacation` (
  `id` int(255) NOT NULL,
  `name` text,
  `date` date DEFAULT NULL,
  `content` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for 课程-2023-2
-- ----------------------------
DROP TABLE IF EXISTS `课程-2023-2`;
CREATE TABLE `课程-2023-2` (
  `教学班编号` varchar(32) COLLATE utf8_bin NOT NULL,
  `学院` varchar(50) COLLATE utf8_bin NOT NULL,
  `课程名` varchar(255) COLLATE utf8_bin NOT NULL,
  `教师` varchar(25) COLLATE utf8_bin DEFAULT NULL,
  `周次` varchar(20) COLLATE utf8_bin DEFAULT NULL,
  `星期` int(11) NOT NULL,
  `开始节次` int(11) DEFAULT NULL,
  `时长节次` int(11) DEFAULT NULL,
  `教学楼` varchar(50) COLLATE utf8_bin DEFAULT NULL,
  `教室` varchar(50) COLLATE utf8_bin DEFAULT NULL,
  `班级` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `学分` varchar(20) COLLATE utf8_bin DEFAULT NULL,
  `考查方式` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`教学班编号`,`课程名`,`星期`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Event structure for vpn_notice_no_pop
-- ----------------------------
DROP EVENT IF EXISTS `vpn_notice_no_pop`;
DELIMITER ;;
CREATE DEFINER=`nuc_info`@`%` EVENT `vpn_notice_no_pop` ON SCHEDULE EVERY 1 DAY STARTS '2023-07-28 07:21:00' ENDS '2024-05-08 07:21:00' ON COMPLETION PRESERVE DISABLE DO UPDATE notice
SET ispop = 0
WHERE id = 3
;;
DELIMITER ;

-- ----------------------------
-- Event structure for vpn_notice_pop
-- ----------------------------
DROP EVENT IF EXISTS `vpn_notice_pop`;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` EVENT `vpn_notice_pop` ON SCHEDULE EVERY 1 DAY STARTS '2023-07-27 23:59:59' ENDS '2024-05-08 23:59:59' ON COMPLETION PRESERVE DISABLE DO UPDATE notice
SET ispop = 1
WHERE id = 3
;;
DELIMITER ;
