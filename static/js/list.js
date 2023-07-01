import { urls } from './common.js'

const yearChoice = $('#yearChoice');
const examChoice = $('#examChoice');
const subjectChoice = $('#subjectChoice');
const problemChoice = $('#problemChoice');
const selectButton = $('#selectButton');

const years = [];
for (let i = 2000; i <= 2030; i++) {
  years.push($('#' * i));
}

const exams = [
    $('#행시'),  // exams[0]: 5급공채/행정고시
    $('#입시'),  // exams[1]: 입법고시
    $('#칠급'),  // exams[2]: 7급공채
    $('#민경'),  // exams[3]: 민간경력
    $('#외시'),  // exams[4]: 외교원/외무고시
    $('#견습'),  // exams[5]: 견습
]

const subs = [
    $('#언어'),  // subs[0]: 언어논리
    $('#자료'),  // subs[1]: 자료해석
    $('#상황'),  // subs[2]: 상황판단
]

function styleOpt(obj, type) {
    type = type === 0 ? 'none' : 'inline';
    obj.forEach(option => {
        if (option !== null) {
            option.css('display', type);
        }
    });
}

function yearFn() {
    switch(yearChoice.val()) {
        case '전체':
            styleOpt([...exams, ...subs], 1);
            break;
        case '2004' || 2004:
            styleOpt([...exams, subs[2]], 0);
            styleOpt([exams[4]], 1);
            break;
        case '2005' || 2005:
            styleOpt(exams, 0);
            styleOpt([...subs, exams[1], exams[4], exams[5]], 1);
            break;
        case '2006' || 2006:
            styleOpt(exams, 0);
            styleOpt([...subs, exams[0], exams[1], exams[5]], 1);
            break;
        case '2007' || 2007:
        case '2008' || 2008:
        case '2009' || 2009:
        case '2010' || 2010:
            styleOpt(exams, 0);
            styleOpt([...subs, exams[0], exams[1]], 1);
            break;
        case '2011' || 2011:
        case '2012' || 2012:
        case '2014' || 2014:
        case '2015' || 2015:
        case '2016' || 2016:
        case '2017' || 2017:
        case '2018' || 2018:
        case '2019' || 2019:
            styleOpt(exams, 0);
            styleOpt([...subs, exams[0], exams[1], exams[3]], 1);
            break;
        case '2013' || 2013:
            styleOpt(exams, 0);
            styleOpt([...subs, exams[0], exams[1], exams[3], exams[4]], 1);
            break;
        case '2020' || 2020:
        case '2021' || 2021:
            styleOpt(exams, 0);
            styleOpt([...subs, ...exams.slice(0, 4)], 1);
            break;
        case '2022' || 2022:
        case '2023' || 2023:
            styleOpt(exams, 0);
            styleOpt([...subs, ...exams.slice(0, 3)], 1);
    }
}

function examFn(obj){
    switch (obj.val()) {
        case '전체':
            styleOpt([...years,...subs], 1);
            break;
        case '외시':
            styleOpt(years, 0);
            styleOpt([years[4], years[5], years[13]], 1);
            break;
        case '견습':
            styleOpt(years, 0);
            styleOpt([years[5], years[6]], 1);
            break;
        case '민경':
            styleOpt(years, 0);
            styleOpt(years.slice(11, 22), 1);
            break;
        case '입시':
            styleOpt(years, 1);
            styleOpt([years[4]], 0);
            break;
        case '칠급':
            styleOpt(years, 0);
            styleOpt(years.slice(20), 1);
            break;
        case '행시':
            styleOpt(years, 1);
            styleOpt([years[4], years[5]], 0);
            break;
    }
}

function subFn(obj){
    styleOpt(years, exams, 1);
    if (obj.val() === '상황') {
        styleOpt([years[4]], 0);
    }
}

yearChoice.on('input', () => {
    yearFn();
});

examChoice.on('input', () => {
    examFn(examChoice);
});

subjectChoice.on('input', () => {
    subFn(subjectChoice);
});

selectButton.on('click', () => {
    if (problemChoice.val()) {
        location.href = `${typeUrl}${problemChoice.val()}/`;
    } else {
        location.href = `${urls['list']}${yearChoice.val()}/${examChoice.val()}/${subjectChoice.val()}/`;
    }
});

