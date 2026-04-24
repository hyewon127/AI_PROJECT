/**
 * 설치 명령어: npm install express multer axios cors form-data
 */
const express = require('express');
const multer = require('multer');
const axios = require('axios');
const cors = require('cors');
const FormData = require('form-data');
const path = require('path');

const app = express();
const PORT = 3000;

// CORS 설정 및 정적 파일 제공 (public 폴더)
app.use(cors());
app.use(express.static('public'));
app.use(express.json());

// 메모리 스토리지 설정 (파일을 디스크에 저장하지 않고 바로 FastAPI로 전달)
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

/**
 * 이미지 분석 요청 프록시 API
 * 클라이언트로부터 이미지와 질문을 받아 FastAPI 서버(8000)로 전달합니다.
 */
app.post('/api/analyze', upload.single('image'), async (req, res) => {
    try {
        const question = req.body.question;
        const file = req.file;

        if (!file) {
            return res.status(400).json({ success: false, message: '이미지 파일이 없습니다.' });
        }

        // FastAPI 서버로 전달할 FormData 생성 (필드명을 FastAPI 매개변수와 일치시킴)
        const form = new FormData();
        form.append('uploadFile', file.buffer, {
            filename: file.originalname,
            contentType: file.mimetype,
        });
        form.append('userQuestion', question);

        // FastAPI 서버(http://localhost:8000/analyze)로 요청 전달
        const response = await axios.post('http://localhost:8000/analyze', form, {
            headers: {
                ...form.getHeaders(),
            },
        });

        // FastAPI로부터 받은 결과를 클라이언트에 반환
        res.json(response.data);
    } catch (error) {
        console.error('Error forwarding request:', error.message);
        res.status(500).json({ 
            success: false, 
            message: 'FastAPI 서버 연결 실패: ' + (error.response?.data?.message || error.message) 
        });
    }
});

// 서버 실행
app.listen(PORT, () => {
    console.log(`================================================`);
    console.log(`웹 서버가 http://localhost:${PORT} 에서 실행 중입니다.`);
    console.log(`FastAPI 서버(8000)가 실행 중인지 확인하세요.`);
    console.log(`================================================`);
});
