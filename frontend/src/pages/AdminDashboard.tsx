import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Autocomplete,
  Chip,
  Alert,
} from '@mui/material';
import { API_BASE_URL } from '../constants/filters';

interface SegmentQuery {
  query: string;
  values: string[];
  count: number;
}

interface SearchAnalytics {
  total_searches: number;
  searches_last_7_days: number;
  searches_last_30_days: number;
  top_queries_by_segment: Record<string, SegmentQuery[]>;
}

interface UnknownExtraction {
  id: number;
  raw_value: string;
  segment: string;
  count: number;
  first_seen: string;
  last_seen: string;
  status: string;
}

interface Industry {
  id: number;
  name: string;
}

export const AdminDashboard = () => {
  const [analytics, setAnalytics] = useState<SearchAnalytics | null>(null);
  const [extractions, setExtractions] = useState<UnknownExtraction[]>([]);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog state
  const [approveDialogOpen, setApproveDialogOpen] = useState(false);
  const [mapDialogOpen, setMapDialogOpen] = useState(false);
  const [selectedExtraction, setSelectedExtraction] = useState<UnknownExtraction | null>(null);
  const [approvedName, setApprovedName] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState<Industry | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch analytics
      const analyticsRes = await fetch(`${API_BASE_URL}/api/admin/search-analytics`);
      const analyticsData = await analyticsRes.json();
      setAnalytics(analyticsData);

      // Fetch unknown extractions
      const extractionsRes = await fetch(`${API_BASE_URL}/api/admin/unknown-industries?status=pending`);
      const extractionsData = await extractionsRes.json();
      setExtractions(extractionsData);

      // Fetch industries for mapping
      const industriesRes = await fetch(`${API_BASE_URL}/api/admin/industries`);
      const industriesData = await industriesRes.json();
      setIndustries(industriesData);

      setError(null);
    } catch (err) {
      setError('Failed to load admin data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedExtraction || !approvedName.trim()) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/approve-industry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          extraction_id: selectedExtraction.id,
          approved_name: approvedName.trim(),
        }),
      });

      if (response.ok) {
        setApproveDialogOpen(false);
        setApprovedName('');
        setSelectedExtraction(null);
        fetchData(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Failed to approve industry');
      }
    } catch (err) {
      alert('Failed to approve industry');
      console.error(err);
    }
  };

  const handleMap = async () => {
    if (!selectedExtraction || !selectedIndustry) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/map-industry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          extraction_id: selectedExtraction.id,
          industry_id: selectedIndustry.id,
        }),
      });

      if (response.ok) {
        setMapDialogOpen(false);
        setSelectedIndustry(null);
        setSelectedExtraction(null);
        fetchData(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Failed to map industry');
      }
    } catch (err) {
      alert('Failed to map industry');
      console.error(err);
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 'bold' }}>
        Admin Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Search Analytics */}
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold' }}>
        Search Analytics
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Searches
              </Typography>
              <Typography variant="h3">{analytics?.total_searches || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Last 7 Days
              </Typography>
              <Typography variant="h3">{analytics?.searches_last_7_days || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Last 30 Days
              </Typography>
              <Typography variant="h3">{analytics?.searches_last_30_days || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Top Queries by Segment */}
      {analytics?.top_queries_by_segment && Object.keys(analytics.top_queries_by_segment).length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Top Queries by Filter
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(analytics.top_queries_by_segment).map(([segment, queries]) => (
              <Grid item xs={12} md={6} key={segment}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" sx={{ mb: 2, textTransform: 'capitalize', fontWeight: 'bold' }}>
                      {segment.replace('_', ' ')}
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Query</TableCell>
                            <TableCell>Values</TableCell>
                            <TableCell align="right">Count</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {queries.map((item, index) => (
                            <TableRow key={index}>
                              <TableCell sx={{ maxWidth: 200 }}>
                                <Typography variant="body2" noWrap title={item.query}>
                                  {item.query}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                  {item.values.map((value, vIndex) => (
                                    <Chip
                                      key={vIndex}
                                      label={value}
                                      size="small"
                                      sx={{ fontSize: '0.7rem' }}
                                    />
                                  ))}
                                </Box>
                              </TableCell>
                              <TableCell align="right">{item.count}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Unknown Industries */}
      <Typography variant="h5" sx={{ mb: 2, mt: 4, fontWeight: 'bold' }}>
        Unknown Industries (LLM Extractions)
      </Typography>
      {extractions.length === 0 ? (
        <Alert severity="info">No pending extractions to review</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Raw Value</TableCell>
                <TableCell>Segment</TableCell>
                <TableCell align="right">Count</TableCell>
                <TableCell>First Seen</TableCell>
                <TableCell>Last Seen</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {extractions.map((extraction) => (
                <TableRow key={extraction.id}>
                  <TableCell>
                    <Chip label={extraction.raw_value} color="warning" />
                  </TableCell>
                  <TableCell>{extraction.segment}</TableCell>
                  <TableCell align="right">{extraction.count}</TableCell>
                  <TableCell>{new Date(extraction.first_seen).toLocaleDateString()}</TableCell>
                  <TableCell>{new Date(extraction.last_seen).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      variant="contained"
                      color="primary"
                      sx={{ mr: 1 }}
                      onClick={() => {
                        setSelectedExtraction(extraction);
                        setApprovedName(extraction.raw_value);
                        setApproveDialogOpen(true);
                      }}
                    >
                      Approve
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => {
                        setSelectedExtraction(extraction);
                        setMapDialogOpen(true);
                      }}
                    >
                      Map
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Approve Dialog */}
      <Dialog open={approveDialogOpen} onClose={() => setApproveDialogOpen(false)}>
        <DialogTitle>Approve New Industry</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Add "{selectedExtraction?.raw_value}" as a new industry
          </Typography>
          <TextField
            autoFocus
            fullWidth
            label="Industry Name"
            value={approvedName}
            onChange={(e) => setApprovedName(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApproveDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleApprove} variant="contained">
            Approve
          </Button>
        </DialogActions>
      </Dialog>

      {/* Map Dialog */}
      <Dialog open={mapDialogOpen} onClose={() => setMapDialogOpen(false)}>
        <DialogTitle>Map to Existing Industry</DialogTitle>
        <DialogContent sx={{ minWidth: 400 }}>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Map "{selectedExtraction?.raw_value}" to an existing industry
          </Typography>
          <Autocomplete
            options={industries}
            getOptionLabel={(option) => option.name}
            value={selectedIndustry}
            onChange={(_, newValue) => setSelectedIndustry(newValue)}
            renderInput={(params) => <TextField {...params} label="Select Industry" />}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMapDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleMap} variant="contained" disabled={!selectedIndustry}>
            Map
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
