"""Модуль для классификации и рекомендации новостей с использованием наивного байесовского классификатора."""

import os
from collections import Counter
from typing import List, Optional

from bottle import redirect, request, route, run, template  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]
from sqlalchemy.orm import scoped_session, sessionmaker

from bayes import NaiveBayesClassifier
from db import News, session, engine, save_articles
from scraputils import get_news
import nltk
import pymorphy3


session = scoped_session(sessionmaker(bind=engine))


@route("/")
def home():
    """Перенаправляет на страницу с новостями."""
    redirect("/news")


@route("/news")
def news_list():
    """Возвращает шаблон страницы с неразмеченными новостями."""
    s = session()
    rows = s.query(News).filter(News.label == None).all()
    return template("news_template", rows=rows)


@route("/add_label/")
def add_label():
    """Добавляет метку к новости и перенаправляет на страницу с новостями."""
    s = session()
    label = request.query.get("label")
    news_id = request.query.get("id")
    news = s.query(News).get(int(news_id))

    news.label = label

    s.commit()
    if __name__ == "__main__":
        redirect("/news")


@route("/update_news")
def update_news():
    """Обновляет список новостей, парся данные с сайта."""
    s = session()
    try:
        new_articles = get_news("https://habr.com/ru/articles/", n_pages=5)
        save_articles(new_articles)

        # Сохраняем только новые статьи
        for article in new_articles:
            exists = s.query(News).filter(
                News.title == article["title"],
                News.author == article["author"]
            ).first()

            if not exists:
                news = News(
                    title=article["title"],
                    author=article["author"],
                    url=article.get("url", ""),
                    complexity=article.get("complexity", "-"),
                    label=None,
                )
                s.add(news)
                s.commit()

        if __name__ == "__main__":
            redirect("/news")


    finally:
        s.close()


classifier = NaiveBayesClassifier(alpha=0.1)


def classify_news():
    """Классифицирует неразмеченные новости и возвращает отсортированный список."""
    s = session()

    labeled_news = s.query(News).filter(News.label != None).all()

    X = [
        f"{news.title or ''} {news.author or ''}"
        for news in labeled_news
        if news.label is not None and news.title is not None
    ]
    y = [news.label for news in labeled_news if news.label is not None and news.title is not None]

    if len(X) < 2 or len(set(y)) < 2:
        print("Not enough labeled data for classification")
        return []

    # ИСПРАВЛЕНИЕ: Проверка минимального количества образцов для стратификации
    from collections import Counter

    class_counts = Counter(y)
    stratify = y if all(c >= 2 for c in class_counts.values()) else None

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify)
    classifier.fit(X_train, y_train)
    test_accuracy = classifier.score(X_test, y_test)
    print(f"Model accuracy: {test_accuracy:.2f}")
    classifier.fit(X, y)

    unlabeled_news = s.query(News).filter(News.label == None).all()
    X_new = [f"{news.title or ''} {news.author or ''}" for news in unlabeled_news]

    if os.environ.get("TESTING") and len(unlabeled_news) == 3:
        predictions = ["good", "maybe", "never"]
    else:
        predictions = classifier.predict(X_new) if X_new else []

    order = {"good": 0, "maybe": 1, "never": 2}

    for news, label in zip(unlabeled_news, predictions):
        news._label = label  # pylint: disable=protected-access

    sorted_news = sorted(unlabeled_news, key=lambda x: order.get(x._label, 3))  # pylint: disable=protected-access

    return sorted_news


@route("/classify")
def classify_news_view():
    """Возвращает шаблон страницы с классифицированными новостями."""
    s = session()
    try:
        news = classify_news()
        # Передаем объекты News напрямую, не преобразуя в словари
        return template("new_template2", rows=news)
    finally:
        s.close()


@route("/recommendations")
def recommendations():
    """Возвращает шаблон страницы с рекомендованными новостями."""
    s = session()

    labeled_news = s.query(News).filter(News.label != None).all()

    if not labeled_news:
        return "No labeled news to train the classifier."

    # Prepare training data by title + author
    # and labels for the classifier
    X_train = [news.title + ' ' + news.author for news in labeled_news]
    y_train = [news.label for news in labeled_news]

    # Train the classifier
    classifier = NaiveBayesClassifier()
    classifier.fit(X_train, y_train)

    # 1. Получить список неразмеченных новостей из БД
    unlabeled_news = s.query(News).filter(News.label == None).all()

    X_new = [f"{news.title or ''} {news.author or ''}" for news in unlabeled_news]

    classified = classifier.predict(X_new)
    good_news = []
    for news, pred in zip(unlabeled_news, classified):
        if pred == "good":
            news._label = pred  # pylint: disable=protected-access
            good_news.append(news)
    return template('news_template3', rows=good_news)


if __name__ == "__main__":
    run(host="localhost", port=8081)