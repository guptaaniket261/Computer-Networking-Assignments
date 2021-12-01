#ifndef TCPNEWRENOCSE_H
#define TCPNEWRENOCSE_H

#include "ns3/tcp-congestion-ops.h"
#include "ns3/tcp-recovery-ops.h"

namespace ns3 {

class TcpNewRenoCSE : public TcpNewReno
{
public:
  static TypeId GetTypeId (void);
  TcpNewRenoCSE (void);
  TcpNewRenoCSE (const TcpNewRenoCSE& sock);
  virtual ~TcpNewRenoCSE (void);
  virtual Ptr<TcpCongestionOps> Fork ();
  virtual std::string GetName () const;

protected:
  virtual uint32_t SlowStart (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);
  virtual void CongestionAvoidance (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);
};

} // namespace ns3

#endif // TCPNEWRENOCSE_H
