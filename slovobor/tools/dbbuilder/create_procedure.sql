# SELECT 
# w.word AS word,w.type AS t 
# FROM words_letters AS s,words AS w 
# WHERE w.length >2 
# AND s.word_id=w.id 
# AND l1<=1 AND … l32<=0 AND l33<=0 AND 1 
# ORDER BY w.length DESC LIMIT 1000

DROP PROCEDURE IF EXISTS GET_WORDS;
SET SESSION group_concat_max_len = 65536;

DELIMITER //

CREATE PROCEDURE GET_WORDS(
    a1 INT, a2 INT, a3 INT, a4 INT, a5 INT, a6 INT,
    a7 INT, a8 INT, a9 INT, a10 INT, a11 INT, a12 INT, a13 INT,
    a14 INT, a15 INT, a16 INT, a17 INT, a18 INT, a19 INT,
    a20 INT, a21 INT, a22 INT, a23 INT, a24 INT, a25 INT,
    a26 INT, a27 INT, a28 INT, a29 INT, a30 INT, a31 INT,
    a32 INT, a33 INT,
    MINLEN INT, MAXRES INT, 
    LANG INT,
    NOUNS_ONLY INT,
    SKIP_OFFENSVE INT)

    BEGIN

        SELECT
        GROUP_CONCAT(w.word SEPARATOR ',') AS 'i',
        COUNT(*) AS 'c'
        FROM words AS w
        
        WHERE 
        w.length >= MINLEN 
        AND (NOT NOUNS_ONLY OR w.morph = 1)
        AND w.topo = 0 
        AND w.nomen = 0 
        AND w.lang = LANG
        AND (NOT SKIP_OFFENSVE OR NOT w.offensive)
        AND l1<=a1 AND l2<=a2 AND l3<=a3 AND l4<=a4 AND l5<=a5 AND l6<=a6 AND l7<=a7 
        AND l8<=a8 AND l9<=a9 AND l10<=a10 AND l11<=a11 AND l12<=a12 AND l13<=a13 
        AND l14<=a14 AND l15<=a15 AND l16<=a16 AND l17<=a17 AND l18<=a18 AND l19<=a19 
        AND l20<=a20 AND l21<=a21 AND l22<=a22 AND l23<=a23 AND l24<=a24 AND l25<=a25 
        AND l26<=a26 AND l27<=a27 AND l28<=a28 AND l29<=a29 AND l30<=a30 AND l31<=a31 
        AND l32<=a32 AND l33<=a33
        LIMIT MAXRES;

    END //

DELIMITER ;

CALL GET_WORDS(0,0,1,3,3,3,3,3,3,3,0,1,0,1,0,0,0,3,0,1,1,0,0,0,5,5,5,5,5,0,0,0,0,5,100,1,0,0);

