# **Sentiment Analysis**

---

#### Build

```
$ s2i build . seldonio/seldon-core-s2i-python3:1.2.1 sentiment-analysis:1.2.1
```

#### Test

```
$ docker run --name "sentiment-analysis" --rm sentiment-analysis:1.2.1
$ docker exec -it sentiment-analysis python SentimentAnalysis_Test.py
```

#### Usage

```
$ docker run --name "sentiment-analysis" --rm -p 5001:5000 sentiment-analysis:1.2.1
$ curl -g http://localhost:5001/predict --data-urlencode 'json={"data": {"names": ["message"], "ndarray": ["All too much of the man-made is ugly, inefficient, depressing chaos."]}}'
```
