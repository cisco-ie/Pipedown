# Router-Connectedness

## Testing

### Unit Tests

```python -m unittest discover router-connectedness.Tests```

For test_bgp_flush.py
``` python -m unittest Tests.test_bgp_flush.FlushBGPTestCase```

### Integration Tests

**Running iPerf Server**

The iPerf server must be running on another router (the router to whom you are trying to connect your link) in order to test iPerf. 

Use following command to launch iPerf:


```iperf -s -B 10.1.1.2 -u```
