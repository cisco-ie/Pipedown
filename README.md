# Router-Connectedness

## Testing

### Unit Tests

```python -m unittest discover router-connectedness.Tests```

### Integration Tests

**Running iPerf Server**

The iPerf server must be running on another router (the router to whom you are trying to connect your link) in order to test iPerf. 

Use following command to launch iPerf:


```iperf -s -B 10.1.1.2 -u```